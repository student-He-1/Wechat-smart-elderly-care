"""测试路由"""
from fastapi import APIRouter, BackgroundTasks
from datetime import datetime
from app.utils.speech import speak

router = APIRouter()

@router.get("", response_model=dict, summary="测试接口")
async def test_api():
    """测试接口，用于前后端联调"""
    return {
        "message": "API测试成功", 
        "data": {"status": "ok", "time": datetime.now().isoformat()}
    }

@router.get("/speak", response_model=dict, summary="测试语音播报")
async def test_speak(background_tasks: BackgroundTasks):
    """测试语音播报功能"""
    test_text = "这是一个测试语音播报功能的消息"
    background_tasks.add_task(speak, test_text)
    return {
        "message": "语音播报测试已触发", 
        "data": {"text": test_text}
    }
