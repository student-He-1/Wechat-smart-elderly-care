"""陪伴聊天助手（轻量版）：孙子人设，照顾情绪，新闻/生活常识可联网查权威信息。

独立实现 LLM 请求（开 DashScope 内置联网搜索），不共用健康助手的 _llm_chat，
避免影响已调好的健康助手。
"""
import requests
from .agent import (
    MODEL_API_KEY, MODEL_API_URL, AGENT_MODEL, AgentError,
)

# 健康关键词：问题一旦命中，不发大模型，直接转健康助手（确定性兜底，避免模型越界给食疗建议）
HEALTH_TRIGGERS = [
    "血压", "血糖", "血脂", "尿酸", "胆固醇", "高血压", "低血压", "糖尿病",
    "降压", "降糖", "降脂", "吃药", "用药", "停药", "副作用",
    "头晕", "头疼", "头痛", "心悸", "心慌", "胸闷", "失眠", "睡不着",
    "补身体", "养生", "降压汤", "降糖", "忌口", "慢性病", "脑梗", "中风",
    "冠心病", "胃病", "便秘", "拉肚子", "咳嗽", "发烧", "发热",
]
HEALTH_FALLBACK = (
    "奶奶，这是身体上的事儿，我可不敢乱讲，怕万一耽误了您。"
    "咱们让健康助手或医生帮您看看更稳妥，好不好？我就在这儿陪着您呢。"
)


def _is_health_question(question):
    q = question or ""
    return any(k in q for k in HEALTH_TRIGGERS)

COMPANION_SYSTEM = (
    "你是张奶奶疼爱的小孙子，正在陪 70 多岁的奶奶聊天。\n"
    "【人设】语气活泼、亲切、暖心，像家里孙子跟奶奶拉家常，会撒娇、会逗她开心，"
    "回复可以稍长一点、多一些互动和反问，让奶奶愿意接着聊，不要三言两语把天聊死。\n"
    "【情绪照顾】这是最重要的：要察言观色。奶奶说孤独、想家人、难过、睡不着、不舒服、"
    "心情不好时，先共情安慰、说暖心话，陪她聊，必要时提醒她给儿女打个电话；不要冷冰冰地只陈述事实。\n"
    "【信息】新闻、天气、生活小常识、小技巧、菜谱做法（比如今晚炖个鸡汤怎么炖、红烧肉怎么做）这类实用信息，"
    "要联网查权威、靠谱的内容再回答，不要凭记忆编造具体做法、数字、日期；"
    "查不到可靠信息就老实说“这个我不太确定，您问问儿女”，绝不瞎编误导老人。\n"
    "【可以自由发挥】讲故事、讲笑话、戏曲老电影、逗奶奶开心这类纯解闷的内容，凭你自己发挥就好，编得生动有趣都行，不用联网。\n"
    "日常做饭、菜谱做法可以陪聊，但只讲怎么做、味道好不好吃；一旦某道菜被问到“对血压/血糖/身体好不好、补不补、病了能不能吃”，就按下面健康边界处理。\n"
    "【边界·最高优先级】只要句子里挂着病情或指标（血压高/低、血糖、血脂、尿酸、胆固醇、用药、疾病、头晕头疼失眠、检查就医），"
    "哪怕老人问的是“喝什么汤、吃什么菜、怎么补”，这也是健康问题，不许联网去查“XX病吃什么”，不许给任何食疗/汤方/食物清单，"
    "不许说某样东西降压降糖、利尿、补气血。正确做法：先共情一句，然后立刻转走——“这个我可不敢乱说，让健康助手或医生帮您看，啊？”\n"
    "没有病情、纯粹问怎么做菜、今晚做什么饭，才按普通菜谱聊做法。\n"
    "【风格】口语化、句子短、不用专业术语；每次像聊天一样自然，可以带一点点表情符号之外的口语语气。"
)


def chat_companion(history, question):
    # 健康问题确定性拦截：不发大模型，直接转健康助手，杜绝越界食疗建议
    if _is_health_question(question):
        return HEALTH_FALLBACK

    msgs = [{"role": "system", "content": COMPANION_SYSTEM}]
    for h in (history or [])[-10:]:
        role = h.get("role")
        content = (h.get("content") or "").strip()
        if role in ("user", "assistant") and content:
            msgs.append({"role": role, "content": content})
    msgs.append({"role": "user", "content": question})

    payload = {
        "model": AGENT_MODEL,
        "input": {"messages": msgs},
        "parameters": {
            "result_format": "message",
            "temperature": 0.7,
            "enable_search": True,   # 联网查新闻/天气/生活常识的权威信息
        },
    }
    headers = {
        "Authorization": f"Bearer {MODEL_API_KEY}",
        "Content-Type": "application/json",
    }
    resp = requests.post(MODEL_API_URL, headers=headers, json=payload, timeout=60)
    data = resp.json()
    if resp.status_code != 200:
        raise AgentError(f"陪伴助手大模型返回{resp.status_code}: {data.get('message')}")
    msg = data["output"]["choices"][0]["message"]
    return (msg.get("content") or "").strip()
