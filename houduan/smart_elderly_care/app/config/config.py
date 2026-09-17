"""配置模块"""
import os
from pathlib import Path
from typing import Optional


def _load_dotenv():
    """从项目根目录（smart_elderly_care/）的 .env 文件加载环境变量。

    优先使用 python-dotenv；未安装时使用内置的简易解析，避免新增依赖。
    密钥只允许存在于 .env（不入库）或系统环境变量中，禁止硬编码在源码里。
    """
    env_path = Path(__file__).resolve().parents[2] / ".env"
    try:
        from dotenv import load_dotenv  # type: ignore
        load_dotenv(env_path)
        return
    except ImportError:
        pass
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()

# 数据库配置
DATABASE_URL = "sqlite:///./smart_elderly_care.db"

# 大模型API配置
# API 密钥从环境变量 / .env 文件读取（变量名 DASHSCOPE_API_KEY），不要在此填写明文
MODEL_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
MODEL_API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
MODEL_NAME = "qwen-turbo"  # 使用正确的模型名称

# Azure TTS API配置（旧方案，已弃用，保留兼容）
# 密钥从环境变量 / .env 文件读取（变量名 AZURE_TTS_KEY）
AZURE_TTS_KEY = os.getenv("AZURE_TTS_KEY", "")
AZURE_TTS_REGION = "eastasia"

# ===== 阿里云 CosyVoice / Qwen-Audio TTS 配置（现行方案）=====
# 与大模型共用同一个 DashScope API Key
TTS_API_URL = "https://dashscope.aliyuncs.com/api/v1/services/audio/tts/SpeechSynthesizer"
TTS_MODEL = "cosyvoice-v3-flash"        # 默认模型（CosyVoice，支持指令切口音）
TTS_VOICE = "longanhuan_v3"             # 默认统一温暖女声
TTS_FORMAT = "mp3"
TTS_SAMPLE_RATE = 22050
# 方言音色方案：统一模型/音色，靠 instruction 切换口音，保证助手是同一把声音。
# 仅保留引擎实测稳定支持的方言；天津话 CosyVoice 报 428、粤语文白夹杂，已移除。
# 某个方言如需天生方言音色，可在该项覆盖 model/voice（instruction 留空）。
TTS_VOICE_PROFILES = {
    "mandarin":  {"model": "cosyvoice-v3-flash", "voice": "longanhuan_v3", "instruction": ""},
    "sichuan":   {"model": "cosyvoice-v3-flash", "voice": "longanhuan_v3", "instruction": "请用四川话表达。"},
    "northeast": {"model": "cosyvoice-v3-flash", "voice": "longanhuan_v3", "instruction": "请用东北话表达。"},
}
TTS_DEFAULT_DIALECT = "mandarin"

# ===== 阿里云 Paraformer 语音识别（ASR）配置 =====
ASR_MODEL = "paraformer-realtime-v2"   # 一句话/短语音识别，支持本地音频文件
ASR_SAMPLE_RATE = 16000                # 建议前端录音采样率 16k
# 方言 -> 语言提示（官话方言统一按中文识别，粤语额外给 yue）
ASR_DIALECT_HINTS = {
    "mandarin": ["zh"],
    "tianjin": ["zh"],
    "sichuan": ["zh"],
    "northeast": ["zh"],
    "cantonese": ["zh", "yue"],
}

# ===== 代码层健康智能体（Agent）配置 =====
AGENT_MODEL = "qwen-flash"          # 主推理模型（function calling 实测稳定，且不随 qwen-plus 下架）
AGENT_MAX_TOOL_ROUNDS = 5           # 单次问答最多工具调用轮数，防止死循环
AGENT_HISTORY_TURNS = 6             # 带入的最近对话轮数（user+assistant 计一轮）
EMBEDDING_API_URL = "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding"
EMBEDDING_MODEL = "text-embedding-v4"
EMBEDDING_DIM = 1024
RAG_TOP_K = 3                       # 每次检索取最相关的知识片段数

# 应用配置
APP_NAME = "智慧养老系统"
APP_VERSION = "1.0.0"
DEBUG = True

# 定时任务配置
MEDICINE_REMINDER_INTERVAL = 60  # 用药提醒检查间隔（秒）

# 日志配置
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
