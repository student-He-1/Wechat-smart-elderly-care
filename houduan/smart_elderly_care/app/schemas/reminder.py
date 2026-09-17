"""提醒设置模式"""
from pydantic import BaseModel
from typing import List, Optional

class ReminderTime(BaseModel):
    """提醒时间模式"""
    time: str

class ReminderSettingBase(BaseModel):
    """提醒设置基础模式"""
    reminder_type: str
    reminder_name: str
    enabled: bool
    times: List[str]

class ReminderSettingCreate(ReminderSettingBase):
    """创建提醒设置模式"""
    pass

class ReminderSettingUpdate(BaseModel):
    """更新提醒设置模式"""
    reminder_name: Optional[str] = None
    enabled: Optional[bool] = None
    times: Optional[List[str]] = None

class ReminderSettingResponse(ReminderSettingBase):
    """提醒设置响应模式"""
    id: int
    user_id: int
    
    class Config:
        from_attributes = True

class ReminderSettingsRequest(BaseModel):
    """批量提醒设置请求模式"""
    reminders: List[ReminderSettingCreate]

class ReminderSettingsResponse(BaseModel):
    """批量提醒设置响应模式"""
    message: str
    data: List[ReminderSettingResponse]