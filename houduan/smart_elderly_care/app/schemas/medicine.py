"""药品数据模型"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class MedicineBase(BaseModel):
    """药品基础模型"""
    name: str
    dosage: str
    time: str

class MedicineCreate(MedicineBase):
    """创建药品模型"""
    pass

class MedicineResponse(MedicineBase):
    """药品响应模型"""
    id: int
    created_at: datetime

    class Config:
        """配置"""
        from_attributes = True
