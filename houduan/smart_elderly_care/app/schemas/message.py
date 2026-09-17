"""消息数据模型"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class MessageSend(BaseModel):
    """发送消息"""
    from_id: int
    to_id: int
    channel: str = "family"           # family/worker/notice
    msg_type: str = "text"            # text/voice/image
    content: str
    from_role: Optional[str] = None
    from_name: Optional[str] = None
    to_role: Optional[str] = None


class MessageRead(BaseModel):
    """标记已读：某接收者把某通道消息全部置为已读"""
    user_id: int
    channel: str
    peer_id: Optional[int] = None     # 可指定会话对象


class MessageResponse(BaseModel):
    id: int
    from_id: int
    from_role: Optional[str] = None
    from_name: Optional[str] = None
    to_id: int
    to_role: Optional[str] = None
    channel: str
    msg_type: str
    content: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
