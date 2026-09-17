"""告警路由：触发 / 列表 / 处理"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.models.database import get_db
from app.schemas.alert import AlertCreate, AlertHandle, AlertResponse
from app.services.alert_service import AlertService
# 占位函数，main.py 启动时会覆盖模块属性为真实 WebSocket 广播（故用模块引用）
from app.services import reminder_service

logger = logging.getLogger(__name__)
router = APIRouter()

_ALERT_TEXT = {
    "sos": "紧急SOS求助",
    "missed_medicine": "漏服药物提醒",
    "bp_high": "血压异常偏高",
    "fall": "检测到跌倒",
}


@router.post("", response_model=AlertResponse, summary="触发告警(如老人SOS)")
def create_alert(payload: AlertCreate, db: Session = Depends(get_db)):
    alert = AlertService.create(db, payload)
    # best-effort 实时推送给在线的子女/社区端
    try:
        reminder_service.send_reminder_to_clients(
            "alert",
            f"{_ALERT_TEXT.get(alert.type, '告警')}：{alert.detail or alert.elder_name or ''}",
            alert.type,
        )
    except Exception as e:
        logger.warning("告警WS推送失败(不影响落库): %s", e)
    return alert


@router.get("", summary="告警列表，可按老人/状态/类型过滤")
def list_alerts(
    elder_id: Optional[int] = None,
    status: Optional[str] = None,
    type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    items = AlertService.list_alerts(db, elder_id, status, type)
    return {"message": "success",
            "data": [AlertResponse.model_validate(a).model_dump() for a in items]}


@router.post("/{alert_id}/handle", response_model=AlertResponse, summary="处理/忽略告警")
def handle_alert(alert_id: int, payload: AlertHandle, db: Session = Depends(get_db)):
    alert = AlertService.handle(db, alert_id, payload)
    if not alert:
        raise HTTPException(status_code=404, detail="告警不存在")
    return alert
