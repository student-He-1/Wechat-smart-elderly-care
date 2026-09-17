"""健康记录数据模型"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class HealthRecordBase(BaseModel):
    """健康记录基础模型：content 与结构化指标至少其一"""
    content: Optional[str] = None


class HealthRecordCreate(HealthRecordBase):
    """创建健康记录（兼容旧的纯文本，也支持结构化）"""
    elder_id: Optional[int] = 1
    record_type: Optional[str] = None      # bp/sugar/heart/weight/temperature
    systolic: Optional[int] = None
    diastolic: Optional[int] = None
    value: Optional[float] = None
    unit: Optional[str] = None
    measured_at: Optional[datetime] = None


class HealthRecordResponse(HealthRecordCreate):
    """健康记录响应模型"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
