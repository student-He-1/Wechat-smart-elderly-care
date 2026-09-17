"""代码层健康智能体路由"""
import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.conversation import Conversation, ChatMessage
from app.schemas.health_agent import AgentChatRequest, BranchRequest
from app.services.agent.agent import run_health_agent, AgentError, stream_health_agent

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat/stream", summary="健康智能体流式对话（逐字返回）")
def chat_stream(payload: AgentChatRequest, db: Session = Depends(get_db)):
    gen = stream_health_agent(
        db, elder_id=payload.elder_id, question=payload.question,
        asker_role=payload.asker_role, session_id=payload.session_id,
        branch_term=payload.branch_term,
    )
    return StreamingResponse(
        gen,
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@router.post("/chat", summary="健康智能体对话（自动检索知识库+调用数据工具）")
def chat(payload: AgentChatRequest, db: Session = Depends(get_db)):
    try:
        result = run_health_agent(
            db, elder_id=payload.elder_id, question=payload.question,
            asker_role=payload.asker_role, session_id=payload.session_id,
        )
    except AgentError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("健康助手异常")
        raise HTTPException(status_code=500, detail=f"健康助手异常: {e}")

    # 工具留痕精简：去掉内部错误堆栈，只保留 工具/参数/结果
    traces = []
    for t in result.tool_traces:
        traces.append({
            "tool": t.get("tool"),
            "arguments": t.get("arguments"),
            "result": t.get("result", t.get("error")),
        })
    return {
        "message": "success",
        "data": {
            "answer": result.answer,
            "session_id": result.session_id,
            "is_emergency": result.is_emergency,
            "tool_traces": traces,          # 演示用：证明它真查了数据库
            "rag_refs": result.rag_refs,    # 演示用：证明它检索了知识库
            "terms": result.terms,          # 子女端：可点开的专业术语（最多1个）
        },
    }


@router.post("/branch", summary="子女端：为某个术语开独立解释分支（不污染主线）")
def open_branch(payload: BranchRequest, db: Session = Depends(get_db)):
    try:
        result = run_health_agent(
            db, elder_id=payload.elder_id, question="",
            asker_role=payload.asker_role,
            session_id=payload.parent_session_id,
            branch_term=payload.term,
        )
    except AgentError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("开术语分支异常")
        raise HTTPException(status_code=500, detail=f"开分支异常: {e}")

    return {
        "message": "success",
        "data": {
            "session_id": result.session_id,   # 新分支会话ID，后续追问复用 /chat
            "anchor_term": payload.term,
            "answer": result.answer,
            "is_emergency": result.is_emergency,
        },
    }


@router.get("/sessions", summary="某老人的历史会话列表")
def list_sessions(elder_id: int = 1, db: Session = Depends(get_db)):
    rows = (db.query(Conversation)
            .filter(Conversation.elder_id == elder_id)
            .order_by(Conversation.id.desc()).all())
    return {"message": "success", "data": [
        {"id": c.id, "title": c.title, "asker_role": c.asker_role,
         "created_at": c.created_at} for c in rows]}


@router.get("/sessions/{session_id}/messages", summary="某次会话的完整消息(含工具调用)")
def session_messages(session_id: int, db: Session = Depends(get_db)):
    rows = (db.query(ChatMessage)
            .filter(ChatMessage.conversation_id == session_id)
            .order_by(ChatMessage.id.asc()).all())
    data = []
    for m in rows:
        data.append({
            "role": m.role, "name": m.name, "content": m.content,
            "tool_calls": json.loads(m.tool_calls) if m.tool_calls else None,
            "created_at": m.created_at,
        })
    return {"message": "success", "data": data}
