"""陪伴聊天助手路由（轻量版，与健康助手隔离）"""
import logging
from typing import List, Optional
from fastapi import APIRouter
from pydantic import BaseModel

from app.services.agent.companion import chat_companion
from app.services.agent.agent import AgentError

logger = logging.getLogger(__name__)
router = APIRouter()


class HistoryMsg(BaseModel):
    role: str
    content: str


class CompanionRequest(BaseModel):
    question: str
    history: Optional[List[HistoryMsg]] = None


@router.post("/chat", summary="陪伴助手聊天（纯闲聊，不查库不挂工具）")
def chat(payload: CompanionRequest):
    history = [h.model_dump() for h in (payload.history or [])]
    try:
        answer = chat_companion(history, payload.question)
        return {"message": "success", "answer": answer}
    except AgentError as e:
        logger.warning("陪伴助手调用失败: %s", e)
        return {"message": "error", "answer": "我这边有点没听清，您再说一遍好吗？"}
