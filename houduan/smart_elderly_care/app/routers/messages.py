"""消息路由：发送 / 会话 / 收件箱 / 未读数 / 已读"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.models.database import get_db
from app.schemas.message import MessageSend, MessageRead, MessageResponse
from app.services.message_service import MessageService

router = APIRouter()


@router.post("/send", response_model=MessageResponse, summary="发送消息")
def send(payload: MessageSend, db: Session = Depends(get_db)):
    return MessageService.send(db, payload)


@router.get("", summary="拉消息：peer_id=会话对象；否则为收件箱")
def list_messages(
    user_id: int,
    peer_id: Optional[int] = None,
    channel: Optional[str] = None,
    db: Session = Depends(get_db),
):
    if peer_id is not None:
        items = MessageService.get_conversation(db, user_id, peer_id)
    else:
        items = MessageService.list_inbox(db, user_id, channel)
    return {"message": "success",
            "data": [MessageResponse.model_validate(m).model_dump() for m in items]}


@router.get("/unread", summary="分通道未读数 family/worker/notice")
def unread(user_id: int, db: Session = Depends(get_db)):
    return {"message": "success", "data": MessageService.unread_count(db, user_id)}


@router.post("/read", summary="标记某通道(可指定会话)已读")
def read(payload: MessageRead, db: Session = Depends(get_db)):
    n = MessageService.mark_read(db, payload.user_id, payload.channel, payload.peer_id)
    return {"message": "已标记已读", "data": {"updated": n}}
