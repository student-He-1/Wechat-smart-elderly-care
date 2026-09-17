"""健康智能体接口数据模型"""
from typing import Optional
from pydantic import BaseModel


class AgentChatRequest(BaseModel):
    question: str
    elder_id: int = 1
    asker_role: str = "elder"        # elder / daughter
    session_id: Optional[int] = None
    branch_term: Optional[str] = None   # 流式开解释分支用


class BranchRequest(BaseModel):
    """子女端点术语开解释分支：挂在 parent_session_id 这条主会话下"""
    parent_session_id: int
    term: str
    elder_id: int = 1
    asker_role: str = "daughter"
