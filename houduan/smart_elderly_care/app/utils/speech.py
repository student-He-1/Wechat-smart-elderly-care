"""语音播报工具（已重构）

现行方案：语音统一由阿里云 TTS 合成，返回音频 URL 给小程序端播放，
后端服务器不再用 os.system / pyttsx3 本地发声（服务器没有扬声器，
本地播放小程序端也听不到）。

- speak(): 供原有 BackgroundTasks 调用，保持函数签名不变，
  内部走云端合成并记录音频 URL，不再本地播放。
- 本地 pyttsx3 仅作为断网时后端自测兜底，需显式 local=True，且延迟导入，
  这样即使环境没装 pyttsx3，整个应用也能正常启动。
"""
import logging
from app.utils.tts import synthesize, TTSError

logger = logging.getLogger(__name__)


def speak(text: str, dialect: str = "mandarin", local: bool = False):
    """语音播报。

    Args:
        text: 要播报的文本
        dialect: 方言 mandarin/tianjin/sichuan/northeast/cantonese
        local: True 时改用本机 pyttsx3 发声（仅后端自测，默认关闭）
    """
    if local:
        return _local_speak(text, dialect)

    # 默认：云端合成，拿到音频 URL（实际播放由前端完成；
    # 后台定时提醒需要把该 URL 经 WebSocket 推给前端，后续接入）
    try:
        result = synthesize(text, dialect)
        logger.info("语音已合成 dialect=%s url=%s", dialect, result.get("audio_url"))
        return result
    except TTSError as e:
        logger.error("云端语音合成失败，跳过播报: %s", e)
        return None


def _local_speak(text: str, dialect: str = "mandarin"):
    """本机 pyttsx3 兜底播报（仅后端自测用，不支持方言音色）。"""
    try:
        import pyttsx3  # 延迟导入，避免缺包导致整个应用无法启动
    except ImportError:
        logger.warning("未安装 pyttsx3，无法本地播报: %s", text)
        return None

    rate_map = {
        "cantonese": 150,
        "northeast": 180,
        "sichuan": 160,
    }
    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", rate_map.get(dialect, 170))
        engine.say(text)
        engine.runAndWait()
        engine.stop()
        logger.info("本地语音播报: %s", text)
    except Exception as e:
        logger.error("本地语音播报失败: %s", e)
    return None
