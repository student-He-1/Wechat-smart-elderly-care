"""用户数据模型"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class UserLogin(BaseModel):
    """演示用登录/切换身份：传 role 即返回或创建账号"""
    role: str                          # elder/daughter/community
    name: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None
    bind_elder_id: Optional[int] = None


class UserResponse(BaseModel):
    id: int
    role: str
    name: str
    phone: Optional[str] = None
    avatar: Optional[str] = None
    bind_elder_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True
