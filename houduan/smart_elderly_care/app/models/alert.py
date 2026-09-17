"""告警模型：SOS / 漏服 / 血压异常 / 跌倒"""
from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from app.models.database import Base


class Alert(Base):
    """告警表

    type:   sos / missed_medicine / bp_high / fall
    level:  red(紧急) / orange(提醒)
    status: unhandled / handled / ignored
    """
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    elder_id = Column(Integer, nullable=False, index=True)     # 哪位老人
    elder_name = Column(String(50))
    type = Column(String(30), nullable=False, index=True)
    level = Column(String(20), default="orange")
    status = Column(String(20), default="unhandled", index=True)
    detail = Column(Text)                                     # 告警描述
    snapshot_url = Column(String(255), nullable=True)         # 跌倒现场截图（静态文件相对路径）
    handler_id = Column(Integer, nullable=True)               # 处理人 user.id
    handled_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    handled_at = Column(DateTime, nullable=True)
