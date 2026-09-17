"""工单数据模型"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class OrderCreate(BaseModel):
    """老人/子女下单"""
    elder_id: int
    service_type: str
    address: Optional[str] = None
    book_time: Optional[str] = None
    remark: Optional[str] = None
    price: Optional[str] = None
    elder_name: Optional[str] = None
    elder_phone: Optional[str] = None
    order_no: Optional[str] = None        # 不传则自动生成


class OrderStatusUpdate(BaseModel):
    """社区端流转状态"""
    status: str                           # pending/ontheway/serving/done
    worker_id: Optional[int] = None


class OrderResponse(BaseModel):
    id: int
    order_no: Optional[str] = None
    elder_id: int
    elder_name: Optional[str] = None
    elder_phone: Optional[str] = None
    service_type: str
    address: Optional[str] = None
    book_time: Optional[str] = None
    status: str
    remark: Optional[str] = None
    price: Optional[str] = None
    worker_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
