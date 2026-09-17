"""健康服务"""
from typing import List
from sqlalchemy.orm import Session
from app.models.health_record import HealthRecord
from app.schemas.health_record import HealthRecordCreate
from app.utils.llm import get_health_answer

class HealthService:
    """健康服务类"""
    
    @staticmethod
    def create_health_record(db: Session, record: HealthRecordCreate) -> HealthRecord:
        """创建健康记录
        
        Args:
            db: 数据库会话
            record: 健康记录创建模型
        
        Returns:
            HealthRecord: 创建的健康记录对象
        """
        # 结构化字段；若未提供文本 content，则按指标自动拼一句
        content = record.content
        if content is None and record.record_type:
            content = HealthService._format_content(record)
        db_record = HealthRecord(
            content=content,
            elder_id=record.elder_id if record.elder_id is not None else 1,
            record_type=record.record_type,
            systolic=record.systolic,
            diastolic=record.diastolic,
            value=record.value,
            unit=record.unit,
            measured_at=record.measured_at,
        )
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        return db_record

    @staticmethod
    def _format_content(record: HealthRecordCreate) -> str:
        """把结构化指标拼成一句可读文本，兼容旧 content 展示。"""
        t = record.record_type
        if t == "bp":
            return f"血压 {record.systolic}/{record.diastolic} mmHg"
        label = {"sugar": "血糖", "heart": "心率", "weight": "体重",
                 "temperature": "体温"}.get(t, t)
        return f"{label} {record.value} {record.unit or ''}".strip()

    
    @staticmethod
    def get_health_records(db: Session) -> List[HealthRecord]:
        """获取所有健康记录
        
        Args:
            db: 数据库会话
        
        Returns:
            List[HealthRecord]: 健康记录列表
        """
        return db.query(HealthRecord).order_by(HealthRecord.created_at.desc()).all()

    @staticmethod
    def list_metrics(db: Session, elder_id: int, record_type: str = None,
                     limit: int = 7) -> List[HealthRecord]:
        """按老人(及指标类型)查最近若干条结构化记录，按测量时间正序便于看趋势。"""
        q = db.query(HealthRecord).filter(HealthRecord.elder_id == elder_id)
        if record_type:
            q = q.filter(HealthRecord.record_type == record_type)
        q = q.filter(HealthRecord.record_type.isnot(None))
        rows = q.order_by(HealthRecord.measured_at.desc(), HealthRecord.id.desc()).limit(limit).all()
        return list(reversed(rows))
    
    @staticmethod
    def get_health_answer(question: str, dialect: str = 'mandarin') -> str:
        """获取健康问答答案
        
        Args:
            question: 健康问题
            dialect: 方言类型
        
        Returns:
            str: 健康问题的答案
        """
        return get_health_answer(question, dialect)
