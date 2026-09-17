"""轻量向量检索：numpy 余弦相似度 Top-K（知识库仅几十条，全量毫秒级）"""
import json
import numpy as np
from typing import List, Tuple


def _cosine_topk(query_vec: List[float],
                 candidates: List[Tuple[int, List[float]]],
                 k: int = 3) -> List[Tuple[int, float]]:
    """candidates: [(chunk_id, vector), ...]；返回 [(chunk_id, score), ...] 降序。"""
    if not candidates:
        return []
    q = np.asarray(query_vec, dtype=np.float32)
    q = q / (np.linalg.norm(q) + 1e-8)

    ids = [cid for cid, _ in candidates]
    mat = np.asarray([v for _, v in candidates], dtype=np.float32)
    norms = np.linalg.norm(mat, axis=1, keepdims=True) + 1e-8
    mat = mat / norms
    scores = mat @ q
    order = np.argsort(scores)[::-1][:k]
    return [(ids[i], float(scores[i])) for i in order]


def loads_vector(s: str) -> List[float]:
    return json.loads(s)
