"""药品模型"""
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.models.database import Base

class Medicine(Base):
    """药品信息表"""
    __tablename__ = "medicines"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)
    dosage = Column(String(100))
    time = Column(String(50))  # 格式：HH:MM
    created_at = Column(DateTime, default=datetime.utcnow)
