"""服药记录模型：每次用药的待服/已服/漏服状态"""
from sqlalchemy import Column, Integer, String, DateTime, Date
from datetime import datetime, date
from app.models.database import Base


class MedicineLog(Base):
    """服药记录表

    status: pending(待服) / taken(已吃) / missed(漏服)
    """
    __tablename__ = "medicine_logs"

    id = Column(Integer, primary_key=True, index=True)
    elder_id = Column(Integer, nullable=False, index=True)
    medicine_id = Column(Integer, nullable=True)             # 关联 medicines.id
    medicine_name = Column(String(100), nullable=False)
    dosage = Column(String(100))
    plan_date = Column(Date, default=date.today, index=True)  # 计划日期
    planned_time = Column(String(50))                         # 计划时间 HH:MM
    status = Column(String(20), default="pending", index=True)
    taken_at = Column(DateTime, nullable=True)                # 实际确认时间
    created_at = Column(DateTime, default=datetime.utcnow)
