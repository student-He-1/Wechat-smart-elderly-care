"""知识库模型：科普文档片段 + 其向量（轻量 RAG）"""
from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from app.models.database import Base


class KnowledgeDoc(Base):
    """知识片段（一篇科普按小标题切成若干 chunk，每 chunk 一行）"""
    __tablename__ = "knowledge_docs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100))                 # 所属文章标题
    category = Column(String(40), index=True)   # 分类：高血压/糖尿病/用药安全...
    chunk_index = Column(Integer, default=0)    # 片段序号
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class KnowledgeEmbedding(Base):
    """知识片段向量（离线 embed 一次落库，检索时不再调 embedding 接口）"""
    __tablename__ = "knowledge_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    chunk_id = Column(Integer, index=True)      # 关联 KnowledgeDoc.id
    model = Column(String(40))                  # 使用的 embedding 模型
    vector = Column(Text, nullable=False)       # JSON 序列化的浮点向量
    created_at = Column(DateTime, default=datetime.utcnow)
