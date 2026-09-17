"""服药记录路由：确认吃药 / 今日记录 / 完成进度"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.schemas.medicine_log import MedicineLogTake, MedicineLogResponse
from app.services.medicine_log_service import MedicineLogService

router = APIRouter()


@router.post("/take", response_model=MedicineLogResponse, summary="老人确认吃药")
def take(payload: MedicineLogTake, db: Session = Depends(get_db)):
    return MedicineLogService.take(db, payload)


@router.get("/today", summary="今日服药记录")
def today(elder_id: int, db: Session = Depends(get_db)):
    items = MedicineLogService.list_today(db, elder_id)
    return {"message": "success",
            "data": [MedicineLogResponse.model_validate(x).model_dump() for x in items]}


@router.get("/progress", summary="今日完成进度")
def progress(elder_id: int, db: Session = Depends(get_db)):
    return {"message": "success", "data": MedicineLogService.today_progress(db, elder_id)}
