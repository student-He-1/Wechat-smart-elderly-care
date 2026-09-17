"""健康问答数据模型"""
from pydantic import BaseModel

class QuestionRequest(BaseModel):
    """健康问答请求模型"""
    question: str
    dialect: str = "mandarin"

class QuestionResponse(BaseModel):
    """健康问答响应模型"""
    question: str
    answer: str
