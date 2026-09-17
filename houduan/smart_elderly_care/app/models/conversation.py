"""健康助手会话模型：多轮对话记忆与工具调用留痕"""
from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from app.models.database import Base


class Conversation(Base):
    """一次健康助手会话（同一老人可被老人本人或子女提问）"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    elder_id = Column(Integer, default=1, index=True)
    asker_role = Column(String(20), default="elder")   # elder / daughter
    title = Column(String(100))
    # 树形分支（仅子女端术语解释用）：parent_id 指向主会话；anchor_term 记录本分支解释的术语
    parent_id = Column(Integer, nullable=True, index=True)
    anchor_term = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ChatMessage(Base):
    """会话内的一条消息

    role: user / assistant / tool
    tool_calls: 当 assistant 发起工具调用时，存工具调用链 JSON（便于演示留痕）
    """
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, index=True)
    role = Column(String(20), nullable=False)
    name = Column(String(60), nullable=True)          # role=tool 时的工具名
    content = Column(Text)
    tool_calls = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
