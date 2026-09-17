"""知识库服务：构建（切片+向量化落库）与检索（Top-K）"""
import json
import logging
import os
import re
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.knowledge import KnowledgeDoc, KnowledgeEmbedding
from app.services.agent.embedding import embed_texts, EmbeddingError
from app.services.agent.vector_store import _cosine_topk
from app.config.config import EMBEDDING_MODEL, RAG_TOP_K

logger = logging.getLogger(__name__)

_EMBED_BATCH = 10  # 每批向量化条数，控制单次请求大小

# 知识语料目录：每个 .txt 为一篇，第一行是分类，空行分隔段落
KNOWLEDGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge")


def _load_articles_from_dir(directory: str) -> List[Tuple[str, str, List[str]]]:
    """扫描目录下的 .txt 文件，解析为 (标题, 分类, [段落]) 列表。
    文件名格式：序号_标题.txt；文件第一行是分类，之后空行分隔段落。"""
    articles = []
    if not os.path.isdir(directory):
        logger.warning("知识目录不存在: %s", directory)
        return articles
    for fname in sorted(os.listdir(directory)):
        if not fname.endswith(".txt"):
            continue
        # 标题：去掉序号前缀和 .txt 后缀
        title = re.sub(r"^\d+_", "", fname[:-4])
        fpath = os.path.join(directory, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            lines = content.split("\n")
            category = lines[0].strip() if lines else "通用"
            # 剩余内容按空行分段
            body = "\n".join(lines[1:]).strip()
            sections = [s.strip() for s in re.split(r"\n\s*\n", body) if s.strip()]
            if sections:
                articles.append((title, category, sections))
                logger.info("加载知识: %s (%s, %d段)", title, category, len(sections))
        except Exception as e:
            logger.warning("解析知识文件失败 %s: %s", fname, e)
    return articles


class KnowledgeService:

    @staticmethod
    def is_built(db: Session) -> bool:
        return db.query(KnowledgeDoc).count() > 0

    @staticmethod
    def build(db: Session) -> dict:
        """幂等构建：从 knowledge/ 目录读取 txt -> 切片 -> 存片段 -> 批量向量化 -> 向量落库。"""
        if KnowledgeService.is_built(db):
            return {"built": False, "reason": "already",
                    "chunks": db.query(KnowledgeDoc).count()}

        articles = _load_articles_from_dir(KNOWLEDGE_DIR)
        if not articles:
            return {"built": False, "reason": "no_articles", "chunks": 0}

        # 1) 切片入库
        docs = []
        for title, category, sections in articles:
            for idx, sec in enumerate(sections):
                doc = KnowledgeDoc(title=title, category=category,
                                   chunk_index=idx, content=sec.strip())
                db.add(doc)
                docs.append(doc)
        db.commit()
        for d in docs:
            db.refresh(d)

        # 2) 分批向量化并落库
        texts = [d.content for d in docs]
        vectors = []
        for i in range(0, len(texts), _EMBED_BATCH):
            vectors.extend(embed_texts(texts[i:i + _EMBED_BATCH]))
        for d, vec in zip(docs, vectors):
            db.add(KnowledgeEmbedding(chunk_id=d.id, model=EMBEDDING_MODEL,
                                      vector=json.dumps(vec, ensure_ascii=False)))
        db.commit()
        logger.info("知识库构建完成：%d 个片段", len(docs))
        return {"built": True, "chunks": len(docs)}

    @staticmethod
    def retrieve(db: Session, query: str, k: Optional[int] = None) -> List[dict]:
        """检索最相关的 k 个知识片段。知识库未建或向量化失败时返回空（不阻断主流程）。"""
        k = k or RAG_TOP_K
        emb_rows = db.query(KnowledgeEmbedding).all()
        if not emb_rows:
            return []
        try:
            qv = embed_texts([query])[0]
        except EmbeddingError as e:
            logger.warning("检索向量化失败，跳过RAG: %s", e)
            return []

        candidates = [(e.chunk_id, json.loads(e.vector)) for e in emb_rows]
        top = _cosine_topk(qv, candidates, k)

        id_to_doc = {d.id: d for d in db.query(KnowledgeDoc).all()}
        result = []
        for chunk_id, score in top:
            d = id_to_doc.get(chunk_id)
            if d:
                result.append({"chunk_id": chunk_id, "title": d.title,
                               "category": d.category, "content": d.content,
                               "score": round(score, 4)})
        return result
