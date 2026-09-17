"""DashScope 文本向量化（embedding）封装"""
import logging
import requests
from typing import List
from app.config.config import (
    MODEL_API_KEY, EMBEDDING_API_URL, EMBEDDING_MODEL, EMBEDDING_DIM,
)

logger = logging.getLogger(__name__)


class EmbeddingError(Exception):
    pass


def embed_texts(texts: List[str]) -> List[List[float]]:
    """批量文本 -> 向量列表（顺序与输入一致）。"""
    if not texts:
        return []
    headers = {"Authorization": f"Bearer {MODEL_API_KEY}", "Content-Type": "application/json"}
    body = {
        "model": EMBEDDING_MODEL,
        "input": {"texts": texts},
        "parameters": {"dimension": EMBEDDING_DIM},
    }
    try:
        resp = requests.post(EMBEDDING_API_URL, headers=headers, json=body, timeout=30)
        data = resp.json()
        if resp.status_code != 200:
            raise EmbeddingError(f"embedding接口返回{resp.status_code}: {data.get('message')}")
        emb = data["output"]["embeddings"]
        # DashScope 按 text_index 排序，稳妥起见排一下
        emb = sorted(emb, key=lambda x: x.get("text_index", 0))
        return [e["embedding"] for e in emb]
    except EmbeddingError:
        raise
    except Exception as e:
        raise EmbeddingError(f"embedding调用异常: {e}") from e


def embed_one(text: str) -> List[float]:
    return embed_texts([text])[0]
