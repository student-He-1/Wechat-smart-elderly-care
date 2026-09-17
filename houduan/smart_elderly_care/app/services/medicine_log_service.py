"""服药记录服务"""
from datetime import datetime, date
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.medicine_log import MedicineLog
from app.schemas.medicine_log import MedicineLogTake


class MedicineLogService:

    @staticmethod
    def take(db: Session, payload: MedicineLogTake) -> MedicineLog:
        """老人确认吃药：当天同药品有待服记录则更新，否则新建已服记录。"""
        today = date.today()
        log = None
        if payload.medicine_id is not None:
            log = (db.query(MedicineLog)
                   .filter(MedicineLog.elder_id == payload.elder_id,
                           MedicineLog.medicine_id == payload.medicine_id,
                           MedicineLog.plan_date == today,
                           MedicineLog.status == "pending")
                   .first())
        if log is None:
            log = MedicineLog(
                elder_id=payload.elder_id,
                medicine_id=payload.medicine_id,
                medicine_name=payload.medicine_name,
                dosage=payload.dosage,
                plan_date=today,
                planned_time=payload.planned_time,
            )
            db.add(log)
        log.status = "taken"
        log.taken_at = datetime.utcnow()
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def list_today(db: Session, elder_id: int,
                   target_date: Optional[date] = None) -> List[MedicineLog]:
        day = target_date or date.today()
        return (db.query(MedicineLog)
                .filter(MedicineLog.elder_id == elder_id,
                        MedicineLog.plan_date == day)
                .order_by(MedicineLog.planned_time.asc())
                .all())

    @staticmethod
    def today_progress(db: Session, elder_id: int) -> dict:
        """今日完成进度：已吃/待服/漏服/总数。"""
        logs = MedicineLogService.list_today(db, elder_id)
        taken = sum(1 for x in logs if x.status == "taken")
        missed = sum(1 for x in logs if x.status == "missed")
        pending = sum(1 for x in logs if x.status == "pending")
        return {
            "date": str(date.today()),
            "total": len(logs),
            "taken": taken,
            "missed": missed,
            "pending": pending,
        }

    @staticmethod
    def mark_missed(db: Session, log_id: int) -> Optional[MedicineLog]:
        log = db.query(MedicineLog).filter(MedicineLog.id == log_id).first()
        if log and log.status == "pending":
            log.status = "missed"
            db.commit()
            db.refresh(log)
        return log
