"""工单模型：社区服务订单（助餐/陪诊/保洁/维修等）"""
from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from app.models.database import Base


class Order(Base):
    """服务工单表

    status: pending(待接单) / ontheway(已接单/出发中) / serving(服务中) / done(已完成)
    """
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String(40), unique=True, index=True)        # 订单号 O20260913001
    elder_id = Column(Integer, nullable=False, index=True)        # 关联老人 user.id
    elder_name = Column(String(50))
    elder_phone = Column(String(20))
    service_type = Column(String(50), nullable=False)             # 上门保洁/陪诊就医...
    address = Column(String(255))
    book_time = Column(String(50))                                # 预约时间（展示文本）
    status = Column(String(20), default="pending", index=True)
    remark = Column(Text)
    price = Column(String(30))
    worker_id = Column(Integer, nullable=True)                    # 接单社区工作人员 user.id
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
