"""服药记录数据模型"""
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel


class MedicineLogTake(BaseModel):
    """老人确认吃药"""
    elder_id: int
    medicine_id: Optional[int] = None
    medicine_name: str
    dosage: Optional[str] = None
    planned_time: Optional[str] = None


class MedicineLogResponse(BaseModel):
    id: int
    elder_id: int
    medicine_id: Optional[int] = None
    medicine_name: str
    dosage: Optional[str] = None
    plan_date: date
    planned_time: Optional[str] = None
    status: str
    taken_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
