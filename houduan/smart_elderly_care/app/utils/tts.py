"""阿里云 CosyVoice 语音合成（TTS）

通过 DashScope 非实时 HTTP 接口把文字合成为语音，
返回一条 24 小时有效的 mp3 URL，由前端（小程序 InnerAudioContext）播放。
每种方言在 config.TTS_VOICE_PROFILES 中配置模型/音色/指令。

内置内存缓存：相同文本+方言第二次请求直接返回缓存 URL，不再调阿里云 API，
首次合成慢（约10字/秒），二次命中毫秒级返回。缓存有效期对齐音频URL的24小时。
"""
import hashlib
import logging
import time

import requests

from app.config.config import (
    MODEL_API_KEY,
    TTS_API_URL,
    TTS_FORMAT,
    TTS_SAMPLE_RATE,
    TTS_VOICE_PROFILES,
    TTS_DEFAULT_DIALECT,
)

logger = logging.getLogger(__name__)

# ============ 内存缓存 ============
_tts_cache = {}
_CACHE_MAX = 500  # 最多缓存条数，防止内存溢出


def _cache_key(dialect: str, text: str) -> str:
    return hashlib.md5(f"{dialect}:{text}".encode("utf-8")).hexdigest()


def _cache_get(dialect: str, text: str):
    """查缓存，命中且未过期返回 result dict，否则返回 None"""
    key = _cache_key(dialect, text)
    entry = _tts_cache.get(key)
    if entry and entry["expires_at"] > time.time():
        return entry["result"]
    if key in _tts_cache:
        del _tts_cache[key]  # 过期清理
    return None


def _cache_set(dialect: str, text: str, result: dict):
    """写入缓存，超容量时清空"""
    if len(_tts_cache) >= _CACHE_MAX:
        _tts_cache.clear()
        logger.info("TTS缓存已满，已清空")
    key = _cache_key(dialect, text)
    expires_at = result.get("expires_at") or int(time.time()) + 86400
    _tts_cache[key] = {"result": result, "expires_at": expires_at}


class TTSError(Exception):
    """语音合成失败"""


def synthesize(text: str, dialect: str = "mandarin", timeout: int = 30) -> dict:
    """把文字合成为语音。

    Args:
        text: 待合成文本
        dialect: mandarin/sichuan/northeast（未知方言自动回退普通话）
        timeout: 请求超时秒数（长文本合成较慢，默认30秒）

    Returns:
        {"audio_url": str, "expires_at": int, "audio_id": str, "dialect": str}
    """
    text = (text or "").strip()
    if not text:
        raise TTSError("待合成文本为空")
    if not MODEL_API_KEY:
        raise TTSError("未配置 DashScope API Key")

    # 先查缓存：相同文本+方言二次请求毫秒级返回
    cached = _cache_get(dialect, text)
    if cached:
        logger.info("TTS缓存命中: dialect=%s 字符数=%d", dialect, len(text))
        return cached

    logger.info("TTS开始(未命中缓存): dialect=%s 字符数=%d", dialect, len(text))

    # 取该方言的音色方案；不支持的方言回退普通话而不是报错
    profile = TTS_VOICE_PROFILES.get(dialect) or TTS_VOICE_PROFILES[TTS_DEFAULT_DIALECT]
    model = profile["model"]
    voice = profile["voice"]
    instruction = (profile.get("instruction") or "").strip()
    used_dialect = dialect if dialect in TTS_VOICE_PROFILES else TTS_DEFAULT_DIALECT

    audio_input = {
        "text": text,
        "voice": voice,
        "format": TTS_FORMAT,
        "sample_rate": TTS_SAMPLE_RATE,
    }
    if instruction:
        audio_input["instruction"] = instruction

    payload = {"model": model, "input": audio_input}
    headers = {
        "Authorization": f"Bearer {MODEL_API_KEY}",
        "Content-Type": "application/json",
    }

    last_err = None
    for attempt in range(3):
        try:
            resp = requests.post(TTS_API_URL, headers=headers, json=payload, timeout=timeout)
            if resp.status_code != 200:
                logger.error("TTS失败 dialect=%s status=%s body=%s",
                             dialect, resp.status_code, resp.text[:500])
                raise TTSError(f"语音合成服务返回 {resp.status_code}: {resp.text[:200]}")
            result = resp.json()
            audio = result.get("output", {}).get("audio", {})
            audio_url = audio.get("url", "")
            if not audio_url:
                raise TTSError("语音合成返回中缺少 audio.url")
            logger.info("TTS成功 dialect=%s model=%s voice=%s 字符=%d",
                        used_dialect, model, voice, len(text))
            result_dict = {
                "audio_url": audio_url,
                "expires_at": audio.get("expires_at"),
                "audio_id": audio.get("id"),
                "dialect": used_dialect,
            }
            # 写入缓存，二次请求直接返回
            _cache_set(dialect, text, result_dict)
            return result_dict
        except requests.exceptions.RequestException as e:
            last_err = e
            logger.warning("TTS网络异常（第%d次）: %s", attempt + 1, e)
            if attempt < 2:
                time.sleep(1.5)
    raise TTSError(f"语音合成网络异常: {last_err}") from last_err
