"""告警服务"""
import os
import base64
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.alert import Alert
from app.models.user import User
from app.schemas.alert import AlertCreate, AlertHandle

# static/alerts 目录（项目根/static/alerts），用于存放跌倒现场截图
_STATIC_ALERT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "static", "alerts")


def _save_snapshot(b64: Optional[str]) -> Optional[str]:
    """把 data:image/jpeg;base64,xxx（或纯 base64）落盘，返回可访问的相对 URL。"""
    if not b64:
        return None
    try:
        raw_b64 = b64.split(",", 1)[1] if b64.strip().startswith("data:") else b64
        data = base64.b64decode(raw_b64)
        os.makedirs(_STATIC_ALERT_DIR, exist_ok=True)
        fname = f"fall_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')[:-3]}.jpg"
        with open(os.path.join(_STATIC_ALERT_DIR, fname), "wb") as f:
            f.write(data)
        return f"/static/alerts/{fname}"
    except Exception:
        return None


class AlertService:

    @staticmethod
    def create(db: Session, payload: AlertCreate) -> Alert:
        # 补老人姓名
        elder_name = payload.elder_name
        if not elder_name:
            elder = db.query(User).filter(User.id == payload.elder_id).first()
            elder_name = elder.name if elder else None
        snapshot_url = _save_snapshot(payload.snapshot)
        alert = Alert(
            elder_id=payload.elder_id,
            elder_name=elder_name,
            type=payload.type,
            level=payload.level,
            detail=payload.detail,
            snapshot_url=snapshot_url,
            status="unhandled",
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert

    @staticmethod
    def list_alerts(db: Session, elder_id: Optional[int] = None,
                    status: Optional[str] = None,
                    alert_type: Optional[str] = None) -> List[Alert]:
        """告警列表，时间倒序。可按老人/状态/类型过滤。"""
        q = db.query(Alert)
        if elder_id is not None:
            q = q.filter(Alert.elder_id == elder_id)
        if status:
            q = q.filter(Alert.status == status)
        if alert_type:
            q = q.filter(Alert.type == alert_type)
        return q.order_by(Alert.created_at.desc(), Alert.id.desc()).all()

    @staticmethod
    def handle(db: Session, alert_id: int, payload: AlertHandle) -> Optional[Alert]:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            return None
        alert.status = payload.action if payload.action in ("handled", "ignored") else "handled"
        alert.handler_id = payload.handler_id
        alert.handled_note = payload.note
        alert.handled_at = datetime.utcnow()
        db.commit()
        db.refresh(alert)
        return alert

    @staticmethod
    def unhandled_count(db: Session, elder_id: Optional[int] = None) -> int:
        q = db.query(Alert).filter(Alert.status == "unhandled")
        if elder_id is not None:
            q = q.filter(Alert.elder_id == elder_id)
        return q.count()
