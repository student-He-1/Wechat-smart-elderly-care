"""提醒设置模型"""
from sqlalchemy import Column, Integer, String, Boolean, JSON
from app.models.database import Base

class ReminderSetting(Base):
    """提醒设置模型"""
    __tablename__ = "reminder_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, default=1)  # 默认用户ID
    reminder_type = Column(String(50), nullable=False)  # 提醒类型
    reminder_name = Column(String(100), nullable=False)  # 提醒名称
    enabled = Column(Boolean, default=True)  # 是否启用
    times = Column(JSON, default=[])  # 提醒时间列表