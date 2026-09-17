"""语音合成数据模型"""
from typing import Optional
from pydantic import BaseModel


class TTSRequest(BaseModel):
    """语音合成请求模型"""
    text: str                                  # 待合成文本
    dialect: str = "mandarin"                  # mandarin/tianjin/sichuan/northeast/cantonese


class TTSResponse(BaseModel):
    """语音合成响应模型"""
    text: str
    dialect: str
    audio_url: str
    expires_at: Optional[int] = None
