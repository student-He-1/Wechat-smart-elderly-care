"""消息模型：三端之间的聊天/通知消息"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from datetime import datetime
from app.models.database import Base


class Message(Base):
    """消息表

    channel:
      family  老人 <-> 子女
      worker  老人 <-> 社区工作人员(王师傅)
      notice  社区/系统通知
    msg_type: text / voice / image
    """
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    from_id = Column(Integer, nullable=False, index=True)      # 发送者 user.id
    from_role = Column(String(20), nullable=False)
    from_name = Column(String(50))                             # 冗余发送者名字，方便展示
    to_id = Column(Integer, nullable=False, index=True)        # 接收者 user.id
    to_role = Column(String(20), nullable=False)
    channel = Column(String(20), nullable=False, index=True)   # family/worker/notice
    msg_type = Column(String(20), default="text")
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, index=True)       # 接收者是否已读
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
