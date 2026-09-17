"""语音识别（ASR）路由"""
import os
import logging
from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from app.utils.asr import transcribe, ASRError

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", summary="语音转文字：上传录音文件，返回识别文本")
async def speech_to_text(
    audio: UploadFile = File(..., description="录音文件(mp3/wav/aac/pcm等)"),
    dialect: str = Form("mandarin"),
    sample_rate: int = Form(16000),
    audio_format: str = Form(""),
):
    """小程序用 wx.uploadFile 上传录音，后端转写为文字。

    前端建议 RecorderManager 格式 wav、采样率 16000、单声道。
    """
    try:
        audio_bytes = await audio.read()
        # 格式优先级：表单显式指定 > 文件名后缀 > 默认 wav
        fmt = (audio_format or "").lower().lstrip(".")
        if not fmt and audio.filename and "." in audio.filename:
            fmt = audio.filename.rsplit(".", 1)[-1].lower()
        if not fmt:
            fmt = "wav"
        logger.info(
            "收到ASR上传 文件名=%s 格式=%s 采样率=%s 字节=%d",
            audio.filename, fmt, sample_rate, len(audio_bytes)
        )
        # 落盘一份用于排查（每次覆盖 last.*）
        try:
            os.makedirs("_asr_debug", exist_ok=True)
            dbg_path = os.path.join("_asr_debug", f"last.{fmt}")
            with open(dbg_path, "wb") as f:
                f.write(audio_bytes)
            logger.info("调试录音已保存: %s", dbg_path)
        except OSError as _e:
            logger.warning("调试录音保存失败: %s", _e)
        if len(audio_bytes) < 200:
            # 录音几乎为空，直接返回空文本而不是调模型
            return {"message": "语音识别成功",
                    "data": {"text": "", "dialect": dialect, "heard": False}}

        text = transcribe(
            audio_bytes,
            audio_format=fmt,
            dialect=dialect,
            sample_rate=sample_rate,
        )
        logger.info("ASR识别结果: '%s'", text)
        return {
            "message": "语音识别成功",
            "data": {"text": text, "dialect": dialect, "heard": bool(text)},
        }
    except ASRError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error("ASR路由异常: %s", e)
        raise HTTPException(status_code=500, detail=f"语音识别失败: {e}")
