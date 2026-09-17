"""阿里云 Paraformer 语音识别（ASR）

接收小程序上传的短语音音频（老人按住说话），同步转写成文字。
使用 paraformer-realtime-v2，可直接识别本地音频文件，无需公网 URL / OSS。

关键：微信开发者工具(Chrome内核)即使指定 wav，录出来其实是 webm/opus；
真机则是标准 wav/mp3/aac。因此识别前统一用 ffmpeg(imageio-ffmpeg) 转成
16k 单声道标准 wav，保证两种环境都能识别。ffmpeg 缺失时降级按原格式识别。
dashscope SDK 延迟导入，未安装时不影响整个应用启动。
"""
import os
import uuid
import tempfile
import logging
import subprocess

from app.config.config import (
    MODEL_API_KEY,
    ASR_MODEL,
    ASR_SAMPLE_RATE,
    ASR_DIALECT_HINTS,
)

logger = logging.getLogger(__name__)


class ASRError(Exception):
    """语音识别失败"""


# 允许的音频格式（与微信 RecorderManager 可输出格式对齐）
_ALLOWED_FORMATS = {"mp3", "wav", "pcm", "aac", "opus", "speex", "webm", "m4a", "ogg"}

_FFMPEG_EXE = None


def _ffmpeg_exe():
    """惰性获取 imageio-ffmpeg 自带的 ffmpeg 可执行路径，拿不到返回 None。"""
    global _FFMPEG_EXE
    if _FFMPEG_EXE is None:
        try:
            import imageio_ffmpeg
            _FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception as e:  # 未安装则降级
            logger.warning("imageio-ffmpeg 不可用，跳过音频归一化: %s", e)
            _FFMPEG_EXE = False
    return _FFMPEG_EXE or None


def _normalize_to_wav16k(audio_bytes: bytes, src_format: str) -> bytes:
    """用 ffmpeg 把任意输入音频转成 16kHz 单声道 PCM wav 字节。

     Raises: ASRError 转换失败或 ffmpeg 不可用
    """
    ff = _ffmpeg_exe()
    if not ff:
        raise ASRError("ffmpeg不可用")
    tmp_in = os.path.join(tempfile.gettempdir(), f"asr_in_{uuid.uuid4().hex}.{src_format}")
    tmp_out = os.path.join(tempfile.gettempdir(), f"asr_out_{uuid.uuid4().hex}.wav")
    try:
        with open(tmp_in, "wb") as f:
            f.write(audio_bytes)
        proc = subprocess.run(
            [ff, "-y", "-hide_banner", "-loglevel", "error",
             "-i", tmp_in, "-ar", "16000", "-ac", "1", "-f", "wav", tmp_out],
            capture_output=True, text=True, timeout=30,
        )
        if proc.returncode != 0 or not os.path.exists(tmp_out):
            raise ASRError(f"ffmpeg转码失败: {proc.stderr[-300:]}")
        with open(tmp_out, "rb") as f:
            return f.read()
    finally:
        for p in (tmp_in, tmp_out):
            try:
                if os.path.exists(p):
                    os.remove(p)
            except OSError:
                pass


def transcribe(audio_bytes: bytes,
               audio_format: str = "wav",
               dialect: str = "mandarin",
               sample_rate: int = ASR_SAMPLE_RATE) -> str:
    """把音频字节识别为文字。

    Args:
        audio_bytes: 音频二进制内容
        audio_format: wav/mp3/aac/webm 等（开发者工具可能是 webm 伪装成 wav）
        dialect: mandarin/sichuan/northeast/cantonese
        sample_rate: 原始声明采样率（归一化后统一用 16k）

    Returns:
        识别出的文本（可能为空串，表示没听清）
    """
    if not audio_bytes:
        raise ASRError("音频内容为空")

    audio_format = (audio_format or "wav").lower().lstrip(".")
    if audio_format not in _ALLOWED_FORMATS:
        audio_format = "wav"

    # 1) 统一转成 16k 单声道 wav；ffmpeg 不在则降级用原始字节
    recog_bytes, recog_format, recog_sr = audio_bytes, audio_format, int(sample_rate or 16000)
    try:
        recog_bytes = _normalize_to_wav16k(audio_bytes, audio_format)
        recog_format, recog_sr = "wav", 16000
        logger.info("音频已归一化为 16k 单声道 wav，字节=%d", len(recog_bytes))
    except ASRError as e:
        logger.warning("未做归一化，按原始格式 %s 识别: %s", audio_format, e)

    try:
        import dashscope
        from dashscope.audio.asr import Recognition, RecognitionCallback
    except ImportError as e:
        raise ASRError("后端未安装 dashscope SDK，无法语音识别") from e

    dashscope.api_key = MODEL_API_KEY
    hints = ASR_DIALECT_HINTS.get(dialect, ["zh"])

    tmp_path = os.path.join(
        tempfile.gettempdir(), f"asr_{uuid.uuid4().hex}.{recog_format}"
    )
    try:
        with open(tmp_path, "wb") as f:
            f.write(recog_bytes)

        class _SilentCallback(RecognitionCallback):
            def on_open(self): pass
            def on_close(self): pass
            def on_event(self, result): pass
            def on_complete(self): pass
            def on_error(self, message):
                logger.error("ASR callback error: %s", message)

        recognition = Recognition(
            model=ASR_MODEL,
            callback=_SilentCallback(),
            format=recog_format,
            sample_rate=recog_sr,
            language_hints=hints,
        )
        result = recognition.call(tmp_path)

        if result.status_code != 200:
            logger.error("ASR失败 status=%s msg=%s output=%s",
                         result.status_code, result.message,
                         getattr(result, "output", None))
            raise ASRError(f"语音识别服务返回 {result.status_code}: {result.message}")

        # 主路径：get_sentence()
        sentences = result.get_sentence() or []
        text = "".join(seg.get("text", "") for seg in sentences).strip()

        # 兜底路径：从 output 原始结构再找一遍
        if not text:
            out = getattr(result, "output", None)
            logger.warning("ASR主路径为空，原始output=%s", out)
            try:
                sent = (out or {}).get("sentence") if isinstance(out, dict) else None
                if isinstance(sent, list):
                    text = "".join(
                        (s.get("text", "") if isinstance(s, dict) else str(s))
                        for s in sent).strip()
                elif isinstance(sent, dict):
                    text = (sent.get("text", "") or "").strip()
            except Exception as _e:
                logger.warning("ASR兜底解析异常: %s", _e)

        logger.info("ASR成功 dialect=%s 格式=%s 句数=%d 文本=%s",
                    dialect, recog_format, len(sentences), text)
        return text
    except ASRError:
        raise
    except Exception as e:
        logger.error("ASR异常: %s", e)
        raise ASRError(f"语音识别异常: {e}") from e
    finally:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except OSError:
            pass
