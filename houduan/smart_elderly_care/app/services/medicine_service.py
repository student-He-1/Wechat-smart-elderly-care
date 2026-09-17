"""药品服务"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.medicine import Medicine
from app.schemas.medicine import MedicineCreate

class MedicineService:
    """药品服务类"""
    
    @staticmethod
    def create_medicine(db: Session, medicine: MedicineCreate) -> Medicine:
        """创建药品
        
        Args:
            db: 数据库会话
            medicine: 药品创建模型
        
        Returns:
            Medicine: 创建的药品对象
        """
        db_medicine = Medicine(
            name=medicine.name,
            dosage=medicine.dosage,
            time=medicine.time
        )
        db.add(db_medicine)
        db.commit()
        db.refresh(db_medicine)
        return db_medicine
    
    @staticmethod
    def get_medicines(db: Session) -> List[Medicine]:
        """获取所有药品
        
        Args:
            db: 数据库会话
        
        Returns:
            List[Medicine]: 药品列表
        """
        return db.query(Medicine).all()
    
    @staticmethod
    def get_medicine_by_id(db: Session, medicine_id: int) -> Optional[Medicine]:
        """根据ID获取药品
        
        Args:
            db: 数据库会话
            medicine_id: 药品ID
        
        Returns:
            Optional[Medicine]: 药品对象
        """
        return db.query(Medicine).filter(Medicine.id == medicine_id).first()
    
    @staticmethod
    def delete_medicine(db: Session, medicine_id: int) -> bool:
        """删除药品
        
        Args:
            db: 数据库会话
            medicine_id: 药品ID
        
        Returns:
            bool: 是否删除成功
        """
        medicine = db.query(Medicine).filter(Medicine.id == medicine_id).first()
        if not medicine:
            return False
        db.delete(medicine)
        db.commit()
        return True
    
    @staticmethod
    def get_medicines_by_time(db: Session, time: str) -> List[Medicine]:
        """根据时间获取药品
        
        Args:
            db: 数据库会话
            time: 时间（格式：HH:MM）
        
        Returns:
            List[Medicine]: 药品列表
        """
        return db.query(Medicine).filter(Medicine.time == time).all()
