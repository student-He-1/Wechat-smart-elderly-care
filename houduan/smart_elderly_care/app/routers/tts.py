"""语音合成（TTS）路由"""
import logging
from fastapi import APIRouter, HTTPException

from app.schemas.tts import TTSRequest, TTSResponse
from app.utils.tts import synthesize, TTSError

logger = logging.getLogger(__name__)
router = APIRouter()

# 支持的方言列表（与 config.TTS_VOICE_PROFILES 对齐）
SUPPORTED_DIALECTS = [
    {"dialect": "mandarin", "name": "普通话"},
    {"dialect": "sichuan", "name": "四川话"},
    {"dialect": "northeast", "name": "东北话"},
]


@router.get("/dialects", summary="获取支持的方言列表")
async def list_dialects():
    return {"message": "获取方言列表成功", "data": SUPPORTED_DIALECTS}


@router.post("", summary="文字转语音，返回可播放的音频URL")
def text_to_speech(req: TTSRequest):
    """把文字合成为方言/普通话语音，返回 24 小时有效的 mp3 URL。

    前端拿到 audio_url 后用 wx.createInnerAudioContext() 播放。
    """
    try:
        result = synthesize(req.text, req.dialect)
        data = TTSResponse(
            text=req.text,
            dialect=result["dialect"],
            audio_url=result["audio_url"],
            expires_at=result.get("expires_at"),
        )
        return {"message": "语音合成成功", "data": data}
    except TTSError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error("TTS路由异常: %s", e)
        raise HTTPException(status_code=500, detail=f"语音合成失败: {e}")
