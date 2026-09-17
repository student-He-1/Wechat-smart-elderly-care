"""工单路由：下单 / 列表 / 详情 / 状态流转"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.models.database import get_db
from app.schemas.order import OrderCreate, OrderStatusUpdate, OrderResponse
from app.services.order_service import OrderService

router = APIRouter()


@router.post("", response_model=OrderResponse, summary="老人/子女下单")
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    return OrderService.create(db, payload)


@router.get("", summary="工单列表：community全部；elder/daughter传elder_id")
def list_orders(
    role: Optional[str] = None,
    status: Optional[str] = None,
    elder_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    items = OrderService.list_orders(db, role, status, elder_id)
    return {"message": "success",
            "data": [OrderResponse.model_validate(o).model_dump() for o in items]}


@router.get("/{order_id}", response_model=OrderResponse, summary="工单详情")
def order_detail(order_id: int, db: Session = Depends(get_db)):
    order = OrderService.get_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")
    return order


@router.post("/{order_id}/status", response_model=OrderResponse, summary="流转状态(接单/出发/服务中/完成)")
def change_status(order_id: int, payload: OrderStatusUpdate, db: Session = Depends(get_db)):
    try:
        order = OrderService.update_status(db, order_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")
    return order
