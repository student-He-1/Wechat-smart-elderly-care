"""药品路由"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from typing import List
from app.models.database import get_db
from app.schemas.medicine import MedicineCreate, MedicineResponse
from app.services.medicine_service import MedicineService
from app.utils.speech import speak

router = APIRouter()

@router.post("", response_model=dict, summary="添加药品信息")
async def add_medicine(
    medicine: MedicineCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """添加药品信息，包括药品名称、服用时间、服用剂量"""
    try:
        db_medicine = MedicineService.create_medicine(db, medicine)
        # 语音播报确认
        background_tasks.add_task(
            speak, 
            f"已添加药品{medicine.name}，服用时间{medicine.time}，剂量{medicine.dosage}"
        )
        return {
            "message": "药品添加成功", 
            "data": MedicineResponse.model_validate(db_medicine)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加药品失败: {str(e)}")

@router.get("", response_model=dict, summary="获取药品列表")
async def get_medicines(db: Session = Depends(get_db)):
    """获取所有药品信息"""
    try:
        medicines = MedicineService.get_medicines(db)
        return {
            "message": "获取药品列表成功", 
            "data": [MedicineResponse.model_validate(med) for med in medicines]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取药品列表失败: {str(e)}")

@router.delete("/{medicine_id}", response_model=dict, summary="删除药品信息")
async def delete_medicine(
    medicine_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """删除指定药品信息"""
    try:
        medicine = MedicineService.get_medicine_by_id(db, medicine_id)
        if not medicine:
            raise HTTPException(status_code=404, detail="药品不存在")
        medicine_name = medicine.name
        success = MedicineService.delete_medicine(db, medicine_id)
        if not success:
            raise HTTPException(status_code=404, detail="药品不存在")
        # 语音播报确认
        background_tasks.add_task(speak, f"已删除药品{medicine_name}")
        return {"message": "药品删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除药品失败: {str(e)}")
