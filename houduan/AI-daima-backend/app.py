import os
import json
import base64
import requests
import logging
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv

# 从同目录 .env 文件加载环境变量（密钥不入库，禁止硬编码）
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 延迟初始化语音引擎，避免在沙箱环境中被阻塞
speech_engine = None

app = Flask(__name__)
CORS(app)

# 智谱 GLM API 密钥：从环境变量 / .env 文件读取（变量名 ZHIPU_API_KEY）
API_KEY = os.getenv("ZHIPU_API_KEY", "")
if not API_KEY:
    logger.warning("未配置 ZHIPU_API_KEY，请在 .env 文件或环境变量中设置后再调用大模型接口")
API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
ASR_URL = "https://open.bigmodel.cn/api/paas/v4/audio/transcriptions"
TTS_URL = "https://open.bigmodel.cn/api/paas/v4/audio/speech"

SYSTEM_PROMPT = """你是一个智能聊天助手，专门为老年人提供陪伴和服务。你的职责包括：
1. 日常聊天，陪伴解闷
2. 讲述故事，回忆往事
3. 提供新闻资讯，了解天下事
4. 播放音乐，放松心情
5. 回答生活常识问题

请用友好、温暖的语气回复，保持简洁明了。对于老年人的需求要耐心倾听，给予积极的回应。"""

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "")
    dialect = data.get("dialect", "mandarin")
    
    if not user_message:
        return jsonify({"error": "消息不能为空"}), 400
    
    try:
        # 根据方言类型设置系统提示
        dialect_prompt = ""
        if dialect == 'cantonese':
            dialect_prompt = "请用粤语回答，使用地道的广东话表达方式。"
        elif dialect == 'tianjin':
            dialect_prompt = "请用天津话回答，使用地道的天津方言表达方式。"
        elif dialect == 'northeast':
            dialect_prompt = "请用东北话回答，使用地道的东北方言表达方式。"
        elif dialect == 'sichuan':
            dialect_prompt = "请用四川话回答，使用地道的四川方言表达方式。"
        
        # 合并系统提示和方言提示
        final_system_prompt = f"{SYSTEM_PROMPT} {dialect_prompt}"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }
        
        payload = {
            "model": "glm-4",
            "messages": [
                {"role": "system", "content": final_system_prompt},
                {"role": "user", "content": user_message}
            ],
            "max_tokens": 1024
        }
        
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        result = response.json()
        
        if "choices" in result:
            ai_reply = result["choices"][0]["message"]["content"]
        elif "content" in result:
            ai_reply = result["content"]
        else:
            ai_reply = str(result)
            
        return jsonify({"reply": ai_reply})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/api/ip", methods=["GET"])
def get_ip():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except:
        ip = '127.0.0.1'
    finally:
        s.close()
    return jsonify({"ip": ip, "port": 5000})

@app.route("/api/asr", methods=["POST"])
def asr():
    if "file" not in request.files:
        return jsonify({"error": "请上传音频文件"}), 400
    
    audio_file = request.files["file"]
    file_data = audio_file.read()
    filename = audio_file.filename
    
    print(f"Received file: {filename}, size: {len(file_data)}")
    
    try:
        # 尝试使用本地语音识别库
        # 在沙箱环境中，我们提供一个模拟的响应
        # 在真实环境中，可以使用SpeechRecognition等库进行语音识别
        
        # 根据音频文件大小返回不同的模拟结果
        # 实际应用中应该使用真实的语音识别
        file_size = len(file_data)
        
        if file_size < 10000:
            simulated_text = "你好"
        elif file_size < 20000:
            simulated_text = "今天天气怎么样"
        elif file_size < 30000:
            simulated_text = "讲个故事吧"
        elif file_size < 40000:
            simulated_text = "播放音乐"
        else:
            simulated_text = "你好，我是智能助手，有什么可以帮助你的吗？"
        
        print(f"Simulated ASR result: {simulated_text}")
        return jsonify({"text": simulated_text})
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 方言音色映射
dialect_voices = {
    "mandarin": "zh-CN-XiaoxiaoNeural",  # 普通话女
    "cantonese": "zh-HK-HiuGaaiNeural",  # 粤语女
    "northeast": "zh-CN-liaoning-XiaobeiNeural",  # 东北话
    "sichuan": "zh-CN-sichuan-YunxiNeural",  # 四川话
    "tianjin": "zh-CN-XiaoxiaoNeural"  # 天津话（暂用普通话）
}

@app.route("/api/tts", methods=["POST"])
def tts():
    data = request.get_json()
    text = data.get("text", "")
    voice = data.get("voice", "female")
    dialect = data.get("dialect", "mandarin")
    
    if not text:
        return jsonify({"error": "文本不能为空"}), 400
    
    try:
        # 尝试使用Azure TTS API
        # 注意：这里需要配置Azure TTS API密钥
        # 实际使用时请替换为真实的API密钥
        AZURE_TTS_KEY = "YOUR_AZURE_TTS_KEY"
        AZURE_TTS_REGION = "eastasia"
        
        if AZURE_TTS_KEY and AZURE_TTS_REGION:
            logger.info(f"使用Azure TTS进行语音播报，方言: {dialect}")
            voice = dialect_voices.get(dialect, "zh-CN-XiaoxiaoNeural")
            
            # Azure TTS API调用
            url = f"https://{AZURE_TTS_REGION}.tts.speech.microsoft.com/cognitiveservices/v1"
            headers = {
                "Ocp-Apim-Subscription-Key": AZURE_TTS_KEY,
                "Content-Type": "application/ssml+xml",
                "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3"
            }
            
            ssml = f"""
            <speak version='1.0' xml:lang='zh-CN'>
                <voice name='{voice}'>
                    {text}
                </voice>
            </speak>
            """
            
            response = requests.post(url, headers=headers, data=ssml.encode('utf-8'), timeout=10)
            
            if response.status_code == 200:
                # 保存音频文件
                audio_file = "temp_speech.mp3"
                with open(audio_file, "wb") as f:
                    f.write(response.content)
                
                # 播放音频文件
                if os.name == 'nt':  # Windows
                    os.system(f"start {audio_file}")
                elif os.name == 'posix':  # macOS/Linux
                    os.system(f"afplay {audio_file}" if os.uname().sysname == 'Darwin' else f"aplay {audio_file}")
                
                logger.info(f"Azure TTS语音播报成功: {text}")
                return jsonify({"message": "语音播报成功"})
            else:
                logger.error(f"Azure TTS API调用失败: {response.status_code}")
        
        # 如果Azure TTS失败或未配置，使用本地pyttsx3
        logger.info(f"使用本地pyttsx3进行语音播报，方言: {dialect}")
        
        # 使用pyttsx3进行本地语音播报
        import pyttsx3
        engine = pyttsx3.init()
        
        # 根据方言调整语音参数
        # 注意：pyttsx3的语音参数调整有限，这里只是简单模拟
        if dialect == "cantonese":
            # 粤语：语速稍慢，语调较高
            engine.setProperty('rate', 150)
        elif dialect == "northeast":
            # 东北话：语速稍快，语调粗犷
            engine.setProperty('rate', 180)
        elif dialect == "sichuan":
            # 四川话：语速中等，语调起伏较大
            engine.setProperty('rate', 160)
        else:
            # 普通话：正常语速和语调
            engine.setProperty('rate', 170)
        
        engine.say(text)
        engine.runAndWait()
        
        # 返回成功消息
        return jsonify({"message": "语音播报成功"})
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)