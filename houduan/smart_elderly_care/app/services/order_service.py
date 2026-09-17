"""工单服务"""
import logging
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.user import User
from app.models.message import Message
from app.schemas.order import OrderCreate, OrderStatusUpdate

logger = logging.getLogger(__name__)

# 允许的状态流转
VALID_STATUS = {"pending", "ontheway", "serving", "done"}


class OrderService:

    @staticmethod
    def _gen_order_no(db: Session) -> str:
        today = datetime.now().strftime("%Y%m%d")
        prefix = f"O{today}"
        count = db.query(Order).filter(Order.order_no.like(f"{prefix}%")).count()
        return f"{prefix}{count + 1:03d}"

    @staticmethod
    def create(db: Session, payload: OrderCreate) -> Order:
        # 补老人信息
        elder_name, elder_phone = payload.elder_name, payload.elder_phone
        if not elder_name:
            elder = db.query(User).filter(User.id == payload.elder_id).first()
            if elder:
                elder_name, elder_phone = elder.name, elder.phone
        order = Order(
            order_no=payload.order_no or OrderService._gen_order_no(db),
            elder_id=payload.elder_id,
            elder_name=elder_name,
            elder_phone=elder_phone,
            service_type=payload.service_type,
            address=payload.address,
            book_time=payload.book_time,
            remark=payload.remark,
            price=payload.price,
            status="pending",
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        return order

    @staticmethod
    def get_by_id(db: Session, order_id: int) -> Optional[Order]:
        return db.query(Order).filter(Order.id == order_id).first()

    @staticmethod
    def list_orders(db: Session, role: Optional[str] = None,
                    status: Optional[str] = None,
                    elder_id: Optional[int] = None) -> List[Order]:
        """工单列表。
        community: 全部工单；elder/daughter: 只看绑定老人的（传 elder_id）。
        """
        q = db.query(Order)
        if status:
            q = q.filter(Order.status == status)
        if elder_id is not None:
            q = q.filter(Order.elder_id == elder_id)
        return q.order_by(Order.created_at.desc(), Order.id.desc()).all()

    @staticmethod
    def update_status(db: Session, order_id: int,
                      payload: OrderStatusUpdate) -> Optional[Order]:
        if payload.status not in VALID_STATUS:
            raise ValueError(f"非法状态: {payload.status}")
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return None

        order.status = payload.status
        if payload.worker_id is not None:
            order.worker_id = payload.worker_id

        # 完成：记完成时间，并给老人 + 绑定子女发消息通知
        if payload.status == "done":
            order.completed_at = datetime.utcnow()
            OrderService._notify_completed(db, order, payload.worker_id)

        db.commit()
        db.refresh(order)
        return order

    @staticmethod
    def _notify_completed(db: Session, order: Order, worker_id: Optional[int]):
        """服务完成：给老人发 worker 消息，给绑定子女发 notice 消息。"""
        worker = None
        if worker_id is not None:
            worker = db.query(User).filter(User.id == worker_id).first()
        worker_name = worker.name if worker else "社区服务人员"
        text = f"您预约的「{order.service_type}」已服务完成，感谢您的使用。"

        # 老人：worker 通道
        db.add(Message(
            from_id=worker_id or 3, from_role="community", from_name=worker_name,
            to_id=order.elder_id, to_role="elder", channel="worker",
            content=text, is_read=False,
        ))

        # 绑定子女：notice 通道（不混进 family 亲情对话）
        children = db.query(User).filter(
            User.role == "daughter",
            User.bind_elder_id == order.elder_id,
        ).all()
        child_text = f"{order.elder_name or '老人'}的「{order.service_type}」工单已由{worker_name}完成。"
        for ch in children:
            db.add(Message(
                from_id=worker_id or 3, from_role="community", from_name=worker_name,
                to_id=ch.id, to_role="daughter", channel="notice",
                content=child_text, is_read=False,
            ))
        logger.info("工单 %s 完成，已通知老人及 %d 位子女", order.order_no, len(children))
