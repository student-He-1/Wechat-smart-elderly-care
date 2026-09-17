"""健康路由"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from typing import List
from app.models.database import get_db
from app.schemas.health_record import HealthRecordCreate, HealthRecordResponse
from app.schemas.question import QuestionRequest, QuestionResponse
from app.schemas.reminder import ReminderSettingCreate, ReminderSettingResponse, ReminderSettingsRequest, ReminderSettingsResponse
from app.services.health_service import HealthService
from app.services.reminder_setting_service import ReminderSettingService
from app.utils.speech import speak

router = APIRouter()

@router.post("/record", response_model=dict, summary="添加健康记录")
async def add_health_record(
    record: HealthRecordCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """添加健康记录，支持语音/文字形式"""
    try:
        db_record = HealthService.create_health_record(db, record)
        # 语音播报确认
        background_tasks.add_task(speak, "健康记录已保存")
        return {
            "message": "健康记录添加成功", 
            "data": HealthRecordResponse.model_validate(db_record)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加健康记录失败: {str(e)}")

@router.get("/record", response_model=dict, summary="获取健康记录列表")
async def get_health_records(db: Session = Depends(get_db)):
    """获取所有健康记录"""
    try:
        records = HealthService.get_health_records(db)
        return {
            "message": "获取健康记录列表成功", 
            "data": [HealthRecordResponse.model_validate(record) for record in records]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取健康记录列表失败: {str(e)}")

@router.post("/metric", response_model=dict, summary="录入结构化健康指标(血压/血糖/心率等)")
async def add_metric(record: HealthRecordCreate, db: Session = Depends(get_db)):
    if not record.record_type:
        raise HTTPException(status_code=400, detail="record_type 不能为空")
    db_record = HealthService.create_health_record(db, record)
    return {"message": "指标已保存", "data": HealthRecordResponse.model_validate(db_record)}


@router.get("/metrics", response_model=dict, summary="按老人/类型查最近健康指标")
async def get_metrics(elder_id: int = 1, record_type: str = None,
                      limit: int = 7, db: Session = Depends(get_db)):
    rows = HealthService.list_metrics(db, elder_id, record_type, limit)
    return {"message": "success",
            "data": [HealthRecordResponse.model_validate(r).model_dump() for r in rows]}


@router.post("/question", response_model=dict, summary="健康问答")
async def health_question(
    question: QuestionRequest,
    background_tasks: BackgroundTasks
):
    """健康问答接口，接收问题文本，返回健康知识"""
    try:
        # 获取健康问答答案（调用大模型API）
        answer = HealthService.get_health_answer(question.question, question.dialect)
        
        # 语音播报回答
        background_tasks.add_task(speak, answer, question.dialect)
        
        return {
            "message": "获取健康知识成功", 
            "data": QuestionResponse(question=question.question, answer=answer)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"健康问答失败: {str(e)}")

@router.get("/reminder-settings", response_model=dict, summary="获取提醒设置")
async def get_reminder_settings(db: Session = Depends(get_db)):
    """获取提醒设置"""
    try:
        settings = ReminderSettingService.get_reminder_settings(db)
        return {
            "message": "获取提醒设置成功", 
            "data": [ReminderSettingResponse.model_validate(setting) for setting in settings]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取提醒设置失败: {str(e)}")

@router.post("/reminder-settings", response_model=dict, summary="保存提醒设置")
async def save_reminder_settings(
    request: ReminderSettingsRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """保存提醒设置"""
    try:
        settings = ReminderSettingService.bulk_create_or_update_reminder_settings(db, request.reminders)
        # 语音播报确认
        background_tasks.add_task(speak, "提醒设置已保存")
        
        # 更新提醒任务
        from app.services.reminder_service import reminder_service
        reminder_service.update_reminder_jobs()
        
        return {
            "message": "保存提醒设置成功", 
            "data": [ReminderSettingResponse.model_validate(setting) for setting in settings]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存提醒设置失败: {str(e)}")
