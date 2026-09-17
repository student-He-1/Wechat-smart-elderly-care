"""健康记录模型

C6 结构化升级：在旧 content 文本字段基础上，新增可查询的指标字段。
旧字段 content 保留，老接口不受影响。
record_type: bp(血压) / sugar(血糖) / heart(心率) / weight(体重) / temperature(体温)
"""
from sqlalchemy import Column, Integer, Float, String, Text, DateTime
from datetime import datetime
from app.models.database import Base


class HealthRecord(Base):
    """健康记录表"""
    __tablename__ = "health_records"

    id = Column(Integer, primary_key=True, index=True)
    # 旧字段（保留兼容，结构化记录可为空）
    content = Column(Text, nullable=True)

    # 新增结构化字段
    elder_id = Column(Integer, default=1, index=True)          # 归属老人
    record_type = Column(String(20), index=True)               # bp/sugar/heart/weight/temperature
    systolic = Column(Integer, nullable=True)                  # 收缩压(高压)
    diastolic = Column(Integer, nullable=True)                 # 舒张压(低压)
    value = Column(Float, nullable=True)                       # 单值指标(血糖/心率/体重/体温)
    unit = Column(String(20), nullable=True)                   # mmHg / mmol/L / 次分 / kg / ℃
    measured_at = Column(DateTime, default=datetime.utcnow, index=True)  # 测量时间

    created_at = Column(DateTime, default=datetime.utcnow)
