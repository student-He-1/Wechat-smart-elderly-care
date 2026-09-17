"""告警数据模型"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AlertCreate(BaseModel):
    """触发告警（如老人 SOS）"""
    elder_id: int
    type: str                                  # sos/missed_medicine/bp_high/fall
    level: str = "orange"                      # red/orange
    detail: Optional[str] = None
    elder_name: Optional[str] = None
    snapshot: Optional[str] = None             # 现场截图（data:image/jpeg;base64,xxx 或纯 base64）


class AlertHandle(BaseModel):
    """处理/忽略告警"""
    handler_id: int
    note: Optional[str] = None
    action: str = "handled"                    # handled/ignored


class AlertResponse(BaseModel):
    id: int
    elder_id: int
    elder_name: Optional[str] = None
    type: str
    level: str
    status: str
    detail: Optional[str] = None
    snapshot_url: Optional[str] = None
    handler_id: Optional[int] = None
    handled_note: Optional[str] = None
    created_at: datetime
    handled_at: Optional[datetime] = None

    class Config:
        from_attributes = True
