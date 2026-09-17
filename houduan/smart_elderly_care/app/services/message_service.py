"""消息服务"""
from typing import List, Optional
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session
from app.models.message import Message
from app.models.user import User
from app.schemas.message import MessageSend


class MessageService:

    @staticmethod
    def send(db: Session, payload: MessageSend) -> Message:
        """发送消息，自动补全双方角色/发送者姓名。"""
        sender = db.query(User).filter(User.id == payload.from_id).first()
        receiver = db.query(User).filter(User.id == payload.to_id).first()

        msg = Message(
            from_id=payload.from_id,
            to_id=payload.to_id,
            channel=payload.channel,
            msg_type=payload.msg_type,
            content=payload.content,
            from_role=payload.from_role or (sender.role if sender else None),
            from_name=payload.from_name or (sender.name if sender else None),
            to_role=payload.to_role or (receiver.role if receiver else None),
            is_read=False,
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)
        return msg

    @staticmethod
    def get_conversation(db: Session, user_id: int, peer_id: int,
                         limit: int = 100) -> List[Message]:
        """拉取 user 与 peer 之间的双向会话，按时间正序。"""
        return (db.query(Message)
                .filter(or_(
                    and_(Message.from_id == user_id, Message.to_id == peer_id),
                    and_(Message.from_id == peer_id, Message.to_id == user_id),
                ))
                .order_by(Message.created_at.asc(), Message.id.asc())
                .limit(limit).all())

    @staticmethod
    def list_inbox(db: Session, user_id: int, channel: Optional[str] = None) -> List[Message]:
        """某用户收到的消息（可按通道过滤），时间倒序。"""
        q = db.query(Message).filter(Message.to_id == user_id)
        if channel:
            q = q.filter(Message.channel == channel)
        return q.order_by(Message.created_at.desc(), Message.id.desc()).all()

    @staticmethod
    def unread_count(db: Session, user_id: int) -> dict:
        """分通道统计未读数：{family:n, worker:n, notice:n, total:n}"""
        result = {"family": 0, "worker": 0, "notice": 0, "total": 0}
        rows = (db.query(Message.channel)
                .filter(Message.to_id == user_id, Message.is_read == False)  # noqa: E712
                .all())
        for (ch,) in rows:
            if ch in result:
                result[ch] += 1
            result["total"] += 1
        return result

    @staticmethod
    def mark_read(db: Session, user_id: int, channel: str,
                  peer_id: Optional[int] = None) -> int:
        """把某用户某通道（可选某会话）的来信标记已读，返回更新条数。"""
        q = db.query(Message).filter(
            Message.to_id == user_id,
            Message.channel == channel,
            Message.is_read == False,  # noqa: E712
        )
        if peer_id is not None:
            q = q.filter(Message.from_id == peer_id)
        n = q.update({Message.is_read: True}, synchronize_session=False)
        db.commit()
        return n
