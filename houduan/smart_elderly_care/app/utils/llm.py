"""大模型调用工具"""
import requests
import logging
from app.config.config import MODEL_API_KEY, MODEL_API_URL, MODEL_NAME

logger = logging.getLogger(__name__)

# 健康知识库（作为大模型的补充，命中关键词直接返回）
health_knowledge = {
    "高血压": "高血压患者应注意低盐饮食，每天盐摄入量不超过5克，定期监测血压，遵医嘱服药，适当运动，保持心情舒畅。",
    "糖尿病": "糖尿病患者应控制饮食，减少糖分摄入，定期监测血糖，适当运动，遵医嘱服药，保持良好的生活习惯。",
    "头晕": "头晕可能由多种原因引起，如低血压、贫血、颈椎病等，建议休息片刻，如症状持续，应及时就医。",
    "失眠": "失眠患者应保持规律的作息时间，睡前避免使用电子设备，可尝试喝温牛奶或听轻音乐助眠。",
    "便秘": "便秘患者应多喝水，多吃蔬菜水果，适当运动，养成定时排便的习惯。",
    "感冒": "感冒患者应多休息，多喝水，保持室内通风，必要时服用感冒药，如症状加重时应及时就医。",
    "咳嗽": "咳嗽患者应多喝水，避免辛辣刺激性食物，保持室内湿度，如咳嗽持续时间较长，应及时就医。",
    "发热": "发热患者应多休息，多喝水，可采取物理降温，如体温超过38.5℃，应及时就医。",
    "关节疼痛": "关节疼痛患者应注意保暖，避免过度劳累，可适当进行热敷，如疼痛持续，应及时就医。",
    "饮食": "老年人饮食应清淡易消化，多吃蔬菜水果，适量摄入蛋白质，少吃油腻和辛辣刺激性食物。",
    "运动": "老年人应适当运动，如散步、太极拳等，避免剧烈运动，运动时应注意安全。",
    "睡眠": "老年人应保持规律的作息时间，每天睡眠时间保持在7-8小时，睡前避免饮用咖啡和茶。",
    "心态": "老年人应保持积极乐观的心态，多与家人朋友交流，参加社交活动，丰富晚年生活。"
}

# 急症关键词：命中后直接给安全兜底，不依赖大模型
EMERGENCY_KEYWORDS = ["胸痛", "胸闷", "晕倒", "昏迷", "大出血", "喘不上气", "呼吸困难",
                      "半身不遂", "嘴歪", "说不出话", "摔了", "摔倒", "跌倒", "站不起来"]

# 方言对应的系统提示
DIALECT_PROMPT = {
    "cantonese": "请用地道的广东话（粤语口语）回答。",
    "tianjin": "请用地道的天津话回答。",
    "northeast": "请用地道的东北话回答。",
    "sichuan": "请用地道的四川话回答。",
}

BASE_SYSTEM_PROMPT = (
    "你是一名社区医院的健康顾问，专门为老年人提供健康咨询服务。"
    "要求：1.语气温和、有耐心；2.用口语化、通俗易懂的表达，不使用专业术语；"
    "3.每次回答不超过100字；4.只做健康科普和生活建议，不做确诊、不开具处方；"
    "5.如症状可能是急症，立即建议联系家人、社区医生或拨打120。"
)

FALLBACK_ANSWER = "抱歉，我暂时无法回答这个问题，建议您咨询专业医生。"


def _call_dashscope(question: str, dialect: str = "mandarin") -> str:
    """以标准 messages 格式调用 DashScope text-generation 接口。"""
    if not (MODEL_API_KEY and MODEL_API_URL):
        return FALLBACK_ANSWER

    system_content = BASE_SYSTEM_PROMPT + DIALECT_PROMPT.get(dialect, "")
    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": question},
    ]
    payload = {
        "model": MODEL_NAME,
        "input": {"messages": messages},
        "parameters": {"result_format": "message"},
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MODEL_API_KEY}",
    }

    try:
        logger.info("调用DashScope，model=%s, dialect=%s, question=%s", MODEL_NAME, dialect, question)
        response = requests.post(MODEL_API_URL, headers=headers, json=payload, timeout=30)
        logger.info("DashScope状态码: %s", response.status_code)
        response.raise_for_status()
        result = response.json()

        # messages 格式返回 output.choices[0].message.content
        choices = result.get("output", {}).get("choices", [])
        if choices:
            answer = choices[0].get("message", {}).get("content", "").strip()
            if answer:
                return answer

        # 兼容旧版 output.text
        text = result.get("output", {}).get("text", "").strip()
        if text:
            return text

        logger.error("DashScope返回结构无法解析: %s", result)
        return FALLBACK_ANSWER
    except requests.exceptions.RequestException as e:
        logger.error("DashScope调用失败: %s；响应: %s", e,
                     getattr(e.response, "text", "无"))
        return FALLBACK_ANSWER


def get_health_answer(question: str, dialect: str = "mandarin") -> str:
    """获取健康问答答案。

    Args:
        question: 健康问题
        dialect: mandarin（普通话）/ cantonese（粤语）/ tianjin（天津话）/
                 northeast（东北话）/ sichuan（四川话）
    """
    try:
        question = (question or "").strip()

        # 1. 急症关键词安全兜底，优先级最高
        for kw in EMERGENCY_KEYWORDS:
            if kw in question:
                return ("您描述的情况可能比较紧急，请先原地休息、不要乱动，"
                        "马上联系身边家人或社区医生，情况严重请立即拨打120。")

        # 2. 普通话优先查本地知识库，命中直接返回
        if dialect == "mandarin":
            for keyword, knowledge in health_knowledge.items():
                if keyword in question:
                    return knowledge

        # 3. 其余情况调用大模型
        return _call_dashscope(question, dialect)
    except Exception as e:
        logger.error("get_health_answer异常: %s", e)
        return FALLBACK_ANSWER
