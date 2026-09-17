"""代码层健康智能体核心：安全层 + RAG + Function-Calling 工具循环 + 多轮记忆

这是整个"代码层智能体"的编排器，不依赖任何 Agent 框架，
用 DashScope 原生 function calling 手写推理-工具循环。
"""
import json
import re
import logging
from dataclasses import dataclass, field
from typing import Optional, List

import requests
from sqlalchemy.orm import Session

from app.config.config import (
    MODEL_API_KEY, MODEL_API_URL, AGENT_MODEL,
    AGENT_MAX_TOOL_ROUNDS, AGENT_HISTORY_TURNS,
)
from app.utils.llm import EMERGENCY_KEYWORDS
from app.services.agent.tool_specs import TOOL_SPECS
from app.services.agent.health_tools import TOOL_REGISTRY
from app.services.agent.knowledge_service import KnowledgeService
from app.models.conversation import Conversation, ChatMessage
from app.models.user import User

logger = logging.getLogger(__name__)


class AgentError(Exception):
    pass


EMERGENCY_REPLY = (
    "您描述的情况可能比较紧急，请先停下手里的事、原地坐下或躺下休息，不要独自活动，"
    "并马上联系身边家人或社区医生；若症状严重，请立即拨打120急救电话。"
)

SYSTEM_PROMPT_BASE = (
    "你是智慧养老平台的健康助手，为老年人及其子女提供健康咨询。请遵守：\n"
    "1. 当需要老人的血压、血糖、心率、体重、今日用药、告警等真实数据时，必须调用提供的工具获取，"
    "绝不允许凭空编造数值；\n"
    "2. 可以结合给出的【参考科普资料】回答，但资料不足时以工具数据为准；\n"
    "3. 只做数据解读、健康科普和生活建议，不下确定诊断、不开具处方、不指导调整处方药剂量，"
    "这类问题要建议咨询医生；\n"
    "4. 说清数值和单位；发现指标明显异常或急症信号，要明确提示联系家人、社区医生或拨打120；\n"
)

# 仅子女端：回答中把一个最关键的专业术语用 {{术语}} 标出，前端可点开看解释
DAUGHTER_MARK_RULE = (
    "【视角】你在和子女（家属）对话，称呼对方用“您”。但所有健康状况、数据、判断的主体都是老人本人，"
    "始终围绕老人展开，例如“张奶奶的血压是…”“张奶奶今天的服药进度…”；"
    "你是在向家属汇报老人的情况，不要把子女本人当成被咨询身体状况的人。\n"
    "【专业表达】回答可以更专业、更结构化：先一句总体判断，再列关键数值与变化趋势，"
    "然后给风险提示和家属可执行的照护建议；可使用专业术语（收缩压、空腹血糖、服药依从性等），"
    "200~300字。\n"
    "【术语标注】本轮回答里如果出现超出日常理解的专业术语，用 {{术语}} 把它们标出来"
    "（例如：您要关注{{收缩压}}和{{心率}}这两个指标）。可标 1~2 个最需要解释的，最多 2 个，"
    "普通词汇、动词、量词一律不要标，没有合适的术语就不要标。\n"
)

ELDER_MARK_RULE = (
    "【语气】你在和老人本人对话，必须口语化、短句、像家人聊天，避免专业术语；"
    "非用不可的术语要顺手打个比方。回答控制在150字以内，条理清楚，结尾告诉老人下一步怎么做。\n"
)

# 术语解释子对话（分支）：只讲清楚一个词，不查实时数据
EXPLAIN_RULE = (
    "【模式】当前是一个术语解释子对话，子女想弄明白刚才那个词。"
    "回答开头先用一句专业、准确的话给出这个术语的医学定义（是什么）；"
    "接着从专业角度说明它为什么重要、家属或照护者日常该怎么观察或配合。"
    "不要点名具体某位老人、不要套用具体老人的病情；语气专业、严谨，"
    "不要过度口语化、不要把术语降维成大白话；不限字数，把是什么、正常值范围、为什么重要、怎么观察讲完整讲透。不调用数据工具。\n"
)
EXPLAIN_MARK_RULE = (
    "【必须再标一个】你的解释里一定会出现另一个专业医学名词，必须用 {{}} 把它包起来，只包一个。"
    "例如解释糖化血红蛋白时，写成：...提示存在{{糖尿病}}或...；解释血压时写成：...会造成{{靶器官}}损害。"
    "注意：你正在解释的这个词本身不要标。一定要输出一个 {{名词}}，不要省略。\n"
)
EXPLAIN_NOMARK_RULE = (
    "【边界】不要再使用 {{}} 标注任何术语，也不要展开新的术语解释，解释就此打住。\n"
)

# 可点术语白名单：模型标注的词必须命中这里，前端才渲染成可点，防止满屏可点
GLOSSARY = {
    "收缩压", "舒张压", "高压", "低压", "空腹血糖", "餐后血糖", "餐后2小时血糖",
    "糖化血红蛋白", "心率", "脉搏", "体质指数", "BMI", "服药依从性", "依从性",
    "临界高血压", "靶器官", "窦性心律", "低血糖", "血压变异性", "同型半胱氨酸",
    "他汀", "阿司匹林", "心律失常", "糖耐量", "血氧饱和度",
    "糖尿病", "2型糖尿病", "胰岛素", "胰岛素抵抗", "肾功能", "肾小球滤过率",
    "蛋白尿", "血肌酐", "冠心病", "心绞痛", "心肌梗死", "房颤", "心力衰竭",
    "动脉粥样硬化", "脑卒中", "中风", "高血压", "高血脂", "胆固醇", "甘油三酯",
    "高密度脂蛋白", "低密度脂蛋白", "骨质疏松", "肌少症", "慢性肾病", "痛风",
    "高尿酸", "尿酸", "甲状腺功能", "甲亢", "甲减", "白内障", "青光眼",
    "压疮", "深静脉血栓", "帕金森", "痴呆", "阿尔茨海默病",
}


@dataclass
class AgentResult:
    answer: str
    session_id: int
    is_emergency: bool = False
    tool_traces: List[dict] = field(default_factory=list)
    rag_refs: List[dict] = field(default_factory=list)
    terms: List[str] = field(default_factory=list)


def _extract_terms(text: str, asker_role: str, allow_mark: bool,
                   max_terms: int = 2, exclude_term: Optional[str] = None):
    """从回答里提取可点术语：仅女儿端、且允许标注时生效，命中白名单。

    allow_mark=False 时（老人端 / 第二层解释），所有 {{}} 还原为普通文字。
    max_terms：主对话最多保留的术语数；解释页传 1。
    exclude_term：解释页里正在解释的那个词，不再重复标注它本身。
    """
    pattern = re.compile(r"{{\s*([^}]+?)\s*}}")
    if asker_role != "daughter" or not allow_mark:
        return pattern.sub(lambda m: m.group(1).strip(), text), []

    hits = [m.strip() for m in pattern.findall(text)]
    chosen = []
    for h in hits:
        if h in GLOSSARY and h != exclude_term and h not in chosen:
            chosen.append(h)
            if len(chosen) >= max_terms:
                break

    chosen_set = set(chosen)

    def _repl(m):
        word = m.group(1).strip()
        return "{{" + word + "}}" if word in chosen_set else word

    cleaned = pattern.sub(_repl, text)
    return cleaned, chosen


def _llm_chat(messages: list, use_tools: bool = True):
    """调用 DashScope，返回 (message_dict, finish_reason)。"""
    parameters = {"result_format": "message", "temperature": 0.3}
    if use_tools:
        parameters["tools"] = TOOL_SPECS
        parameters["tool_choice"] = "auto"
    payload = {"model": AGENT_MODEL, "input": {"messages": messages}, "parameters": parameters}
    headers = {"Authorization": f"Bearer {MODEL_API_KEY}", "Content-Type": "application/json"}
    try:
        resp = requests.post(MODEL_API_URL, headers=headers, json=payload, timeout=40)
        data = resp.json()
        if resp.status_code != 200:
            raise AgentError(f"大模型返回{resp.status_code}: {data.get('message')}")
        choice = data["output"]["choices"][0]
        return choice["message"], choice.get("finish_reason", "stop")
    except AgentError:
        raise
    except Exception as e:
        raise AgentError(f"大模型调用异常: {e}") from e


def _hit_emergency(question: str) -> bool:
    return any(kw in question for kw in EMERGENCY_KEYWORDS)


def _get_or_create_conversation(db: Session, elder_id: int, asker_role: str,
                                session_id: Optional[int], question: str) -> Conversation:
    if session_id:
        conv = db.query(Conversation).filter(Conversation.id == session_id).first()
        if conv:
            return conv
    conv = Conversation(elder_id=elder_id, asker_role=asker_role,
                        title=question[:20])
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def _history_messages(db: Session, conversation_id: int) -> list:
    """取最近若干轮 user/assistant 文本消息（工具内部消息不带入下一轮）。"""
    rows = (db.query(ChatMessage)
            .filter(ChatMessage.conversation_id == conversation_id,
                    ChatMessage.role.in_(["user", "assistant"]),
                    ChatMessage.content.isnot(None))
            .order_by(ChatMessage.id.desc())
            .limit(AGENT_HISTORY_TURNS * 2).all())
    rows = list(reversed(rows))
    return [{"role": r.role, "content": r.content} for r in rows]


def _execute_tool(db: Session, tool_call: dict, elder_id: int) -> (str, dict):
    """执行一次工具调用，返回 (给模型的结果字符串, 留痕dict)。"""
    fn = tool_call.get("function", {})
    name = fn.get("name")
    raw_args = fn.get("arguments", "{}") or "{}"
    try:
        args = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
    except json.JSONDecodeError:
        args = {}
    # elder_id 始终以后端会话绑定的老人为准，防止模型传错
    args["elder_id"] = elder_id

    trace = {"tool": name, "arguments": args}
    func = TOOL_REGISTRY.get(name)
    if func is None:
        trace["error"] = "工具不存在"
        return json.dumps({"error": f"未知工具 {name}"}, ensure_ascii=False), trace
    try:
        result = func(db, **args)
        trace["result"] = result
        return json.dumps(result, ensure_ascii=False), trace
    except Exception as e:
        logger.exception("工具 %s 执行失败", name)
        trace["error"] = str(e)
        return json.dumps({"error": f"工具执行失败: {e}"}, ensure_ascii=False), trace


def run_health_agent(db: Session, elder_id: int, question: str,
                     asker_role: str = "elder",
                     session_id: Optional[int] = None,
                     branch_term: Optional[str] = None) -> AgentResult:
    question = (question or "").strip()
    if branch_term:
        # 开术语解释分支：新建挂在父会话下的子会话，首轮直接让模型解释该术语
        question = f"请用子女能懂的方式，解释术语「{branch_term}」：一句话定义、为什么重要、照护上怎么做。"

    if not question:
        raise AgentError("问题不能为空")

    # 1) 会话 + 落用户消息
    if branch_term and session_id:
        parent = db.query(Conversation).filter(Conversation.id == session_id).first()
        is_level2 = bool(parent and parent.parent_id)   # 父会话本身已是分支 => 这是第二层，不再标术语
        conv = Conversation(elder_id=elder_id, asker_role=asker_role,
                            title=f"术语解释：{branch_term}",
                            parent_id=session_id, anchor_term=branch_term)
        db.add(conv)
        db.commit()
        db.refresh(conv)
    else:
        conv = _get_or_create_conversation(db, elder_id, asker_role, session_id, question)
        is_level2 = False
    is_explain = bool(conv.anchor_term)
    db.add(ChatMessage(conversation_id=conv.id, role="user", content=question))
    db.commit()

    # 2) 安全层：急症直接兜底，不调模型、不调工具
    if _hit_emergency(question):
        db.add(ChatMessage(conversation_id=conv.id, role="assistant",
                           content=EMERGENCY_REPLY))
        db.commit()
        return AgentResult(answer=EMERGENCY_REPLY, session_id=conv.id, is_emergency=True)

    # 3) RAG：不再无条件检索，改为通过 search_knowledge 工具按需调用
    rag_refs = []
    rag_text = ""

    # 4) 组装消息：系统(人设+老人身份+RAG) + 多轮历史 + 本轮问题
    elder = db.query(User).filter(User.id == elder_id).first()
    identity = ""
    if elder:
        identity += f"\n当前咨询涉及的老人姓名是「{elder.name}」，称呼老人时请使用该姓名，不要叫爷爷/奶奶等其他称呼。"
    identity += ("\n本次提问者是老人本人，请直接对老人说话。" if asker_role == "elder"
                 else "\n本次提问者是老人的子女/家属（不是老人本人）。请用“您”称呼家属，"
                      "所有健康状况与建议都围绕老人本人展开，你在向家属汇报老人的情况，语气专业。")
    # 允许标注术语：女儿端 且 不是第二层（第一层解释可再开一个分支）
    allow_mark = (asker_role == "daughter") and not is_level2
    if is_explain:
        role_rule = EXPLAIN_RULE + (EXPLAIN_MARK_RULE if allow_mark else EXPLAIN_NOMARK_RULE)
    elif asker_role == "daughter":
        role_rule = DAUGHTER_MARK_RULE
    else:
        role_rule = ELDER_MARK_RULE
    messages = [{"role": "system", "content": SYSTEM_PROMPT_BASE + role_rule + identity + rag_text}]
    messages.extend(_history_messages(db, conv.id))
    messages.append({"role": "user", "content": question})

    # 5) 回答：解释子对话不查工具、一轮出结果；主对话走工具循环
    tool_traces = []
    answer = ""
    if is_explain:
        message, _ = _llm_chat(messages, use_tools=False)
        answer = (message.get("content") or "").strip()
    else:
        for round_idx in range(AGENT_MAX_TOOL_ROUNDS):
            message, finish = _llm_chat(messages, use_tools=True)
            tool_calls = message.get("tool_calls")

            if not tool_calls:
                answer = (message.get("content") or "").strip()
                break

            # 把发起工具调用的 assistant 消息原样回传
            messages.append(message)
            for tc in tool_calls:
                tool_result, trace = _execute_tool(db, tc, elder_id)
                tool_traces.append(trace)
                messages.append({
                    "role": "tool",
                    "name": tc.get("function", {}).get("name"),
                    "content": tool_result,
                })
        else:
            # 达到工具轮数上限：去掉工具，要求模型基于已有结果收尾，避免死循环
            messages.append({"role": "user",
                             "content": "请基于以上已获取的数据直接给出最终回答，不要再调用工具。"})
            message, _ = _llm_chat(messages, use_tools=False)
            answer = (message.get("content") or "").strip()

    # 术语提取（女儿端：主对话最多2个术语；解释页只再标1个新术语，且不重复标注正在解释的词本身）
    answer, terms = _extract_terms(answer, asker_role, allow_mark,
                                   max_terms=1 if conv.anchor_term else 3,
                                   exclude_term=conv.anchor_term)

    if not answer:
        answer = "抱歉，我暂时没能整理出结论，建议您咨询社区医生，或稍后再问一次。"

    # 6) 落助手消息（含工具调用留痕）
    db.add(ChatMessage(
        conversation_id=conv.id, role="assistant", content=answer,
        tool_calls=json.dumps(tool_traces, ensure_ascii=False) if tool_traces else None))
    db.commit()

    # rag_refs 只回传必要字段
    rag_slim = [{"title": r["title"], "category": r["category"], "score": r["score"]}
                for r in rag_refs]
    return AgentResult(answer=answer, session_id=conv.id,
                       is_emergency=False, tool_traces=tool_traces,
                       rag_refs=rag_slim, terms=terms)


def _llm_chat_stream(messages: list, thinking: bool = False):
    """流式调用 DashScope，逐段 yield (kind, text)。kind=reasoning 为思考过程，delta 为正式回答。"""
    parameters = {"result_format": "message", "temperature": 0.3}
    if thinking:
        # thinking 模式流式必须开 incremental_output，否则 400；开后 content/reasoning_content 均为增量
        parameters["enable_thinking"] = True
        parameters["incremental_output"] = True
    payload = {"model": AGENT_MODEL, "input": {"messages": messages},
               "parameters": parameters, "stream": True}
    headers = {"Authorization": f"Bearer {MODEL_API_KEY}", "Content-Type": "application/json",
               "X-DashScope-SSE": "enable"}
    resp = requests.post(MODEL_API_URL, headers=headers, json=payload, stream=True, timeout=90)
    if resp.status_code != 200:
        raise AgentError(f"流式大模型返回{resp.status_code}")
    last_c = 0
    for raw in resp.iter_lines(decode_unicode=True):
        if not raw:
            continue
        line = raw.strip()
        if not line.startswith("data:"):
            continue
        data_str = line[5:].strip()
        if data_str == "[DONE]":
            break
        try:
            obj = json.loads(data_str)
        except json.JSONDecodeError:
            continue
        choices = obj.get("output", {}).get("choices", [])
        if not choices:
            continue
        msg = choices[0].get("message") or {}
        reasoning = msg.get("reasoning_content") or ""
        content = msg.get("content") or ""
        if thinking:
            # 增量模式：每段即新增，直接下发
            if reasoning:
                yield ("reasoning", reasoning)
            if content:
                yield ("delta", content)
        else:
            # 默认累积模式：只发新增部分
            if content and len(content) > last_c:
                yield ("delta", content[last_c:])
                last_c = len(content)


def _sse(event: str, data: dict) -> str:
    return f"data: {json.dumps({'event': event, **data}, ensure_ascii=False)}\n\n"


def stream_health_agent(db: Session, elder_id: int, question: str,
                        asker_role: str = "elder",
                        session_id: Optional[int] = None,
                        branch_term: Optional[str] = None):
    """流式版本：工具循环非流式跑完，最终回答逐字推给前端。"""
    question = (question or "").strip()
    if branch_term:
        question = (f"请用子女能懂的方式，解释术语「{branch_term}」：一句话定义、"
                    f"为什么重要、照护上怎么做。")
    if not question:
        return

    # 会话
    if branch_term and session_id:
        parent = db.query(Conversation).filter(Conversation.id == session_id).first()
        is_level2 = bool(parent and parent.parent_id)
        conv = Conversation(elder_id=elder_id, asker_role=asker_role,
                            title=f"术语解释：{branch_term}",
                            parent_id=session_id, anchor_term=branch_term)
        db.add(conv)
        db.commit()
        db.refresh(conv)
    else:
        conv = _get_or_create_conversation(db, elder_id, asker_role, session_id, question)
        is_level2 = False
    is_explain = bool(conv.anchor_term)
    db.add(ChatMessage(conversation_id=conv.id, role="user", content=question))
    db.commit()

    # 急症：一次性推
    if _hit_emergency(question):
        db.add(ChatMessage(conversation_id=conv.id, role="assistant", content=EMERGENCY_REPLY))
        db.commit()
        yield _sse("delta", {"text": EMERGENCY_REPLY})
        yield _sse("end", {"session_id": conv.id, "terms": [], "is_emergency": True,
                           "answer": EMERGENCY_REPLY})
        return

    # RAG：不再无条件检索，改为通过 search_knowledge 工具按需调用
    # （LLM 在工具循环中判断是否需要查知识库，需要才调用，避免浪费请求和污染上下文）
    rag_refs = []
    rag_text = ""

    elder = db.query(User).filter(User.id == elder_id).first()
    if is_explain:
        # 术语解释页：纯专业解释，不绑定任何具体老人姓名
        identity = ("\n本次提问者是家属/照护者，你在为 ta 解释一个专业医学术语。"
                    "用专业、通用的语言讲解，不要点名任何具体老人、不要套用某位老人的病情。")
    else:
        identity = ""
        if elder:
            identity += f"\n当前咨询涉及的老人姓名是「{elder.name}」，称呼老人时请使用该姓名。"
        identity += ("\n本次提问者是老人本人，请直接对老人说话。" if asker_role == "elder"
                     else "\n本次提问者是老人的女儿/家属李女士。硬性要求：被照护的老人始终是张奶奶，"
                          "回答中一切健康数据、服药、风险、建议都围绕张奶奶展开；用「您」称呼李女士，"
                          "您是在向女儿汇报张奶奶的情况，绝不能把李女士当成被照护对象，也不要说「您血压如何」。")
    allow_mark = (asker_role == "daughter") and not is_level2
    if is_explain:
        role_rule = EXPLAIN_RULE + (EXPLAIN_MARK_RULE if allow_mark else EXPLAIN_NOMARK_RULE)
    elif asker_role == "daughter":
        role_rule = DAUGHTER_MARK_RULE
    else:
        role_rule = ELDER_MARK_RULE
    messages = [{"role": "system", "content": SYSTEM_PROMPT_BASE + role_rule + identity + rag_text}]
    messages.extend(_history_messages(db, conv.id))
    messages.append({"role": "user", "content": question})

    # 工具循环（非流式）：把数据喂齐
    tool_traces = []
    if not is_explain:
        for _ in range(AGENT_MAX_TOOL_ROUNDS):
            message, finish = _llm_chat(messages, use_tools=True)
            tool_calls = message.get("tool_calls")
            if not tool_calls:
                messages.append(message)
                break
            messages.append(message)
            for tc in tool_calls:
                tool_result, trace = _execute_tool(db, tc, elder_id)
                tool_traces.append(trace)
                messages.append({"role": "tool",
                                 "name": tc.get("function", {}).get("name"),
                                 "content": tool_result})
        else:
            messages.append({"role": "user",
                             "content": "请基于以上已获取的数据直接给出最终回答，不要再调用工具。"})

    # 流式最终回答：仅子女端主线对话开启思考模式；术语解释页(is_explain)不开，下定义不需要推理，直接快出字
    use_thinking = (asker_role == "daughter") and not is_explain
    full = ""
    try:
        for kind, part in _llm_chat_stream(messages, thinking=use_thinking):
            if kind == "reasoning":
                yield _sse("reasoning", {"text": part})
            else:
                full += part
                yield _sse("delta", {"text": part})
    except AgentError as e:
        yield _sse("delta", {"text": f"\n（服务暂时开小差：{e}）"})
        full = full or "抱歉，暂时没能给出回答，请稍后再试。"

    answer, terms = _extract_terms(full, asker_role, allow_mark,
                                   max_terms=1 if conv.anchor_term else 3,
                                   exclude_term=conv.anchor_term)
    db.add(ChatMessage(conversation_id=conv.id, role="assistant", content=answer,
                       tool_calls=json.dumps(tool_traces, ensure_ascii=False) if tool_traces else None))
    db.commit()
    yield _sse("end", {"session_id": conv.id, "terms": terms, "is_emergency": False,
                       "answer": answer,
                       "tool_traces": tool_traces,
                       "rag_refs": [{"title": r["title"], "category": r["category"], "score": r["score"]} for r in rag_refs]})
