"""用户服务"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserLogin

# 演示身份的默认姓名
DEFAULT_NAME = {
    "elder": "张奶奶",
    "daughter": "李女士",
    "community": "王师傅",
}


class UserService:

    @staticmethod
    def login_or_create(db: Session, payload: UserLogin) -> User:
        """演示登录：同 role 已存在则返回第一个，否则创建。"""
        if payload.role not in ("elder", "daughter", "community"):
            raise ValueError("role 必须是 elder/daughter/community")

        user = db.query(User).filter(User.role == payload.role).first()
        if user:
            # 可更新称呼/头像/绑定关系
            if payload.name:
                user.name = payload.name
            if payload.avatar is not None:
                user.avatar = payload.avatar
            if payload.bind_elder_id is not None:
                user.bind_elder_id = payload.bind_elder_id
            db.commit()
            db.refresh(user)
            return user

        user = User(
            role=payload.role,
            name=payload.name or DEFAULT_NAME.get(payload.role, "用户"),
            phone=payload.phone,
            avatar=payload.avatar,
            bind_elder_id=payload.bind_elder_id,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def list_by_role(db: Session, role: str) -> List[User]:
        return db.query(User).filter(User.role == role).all()

    @staticmethod
    def list_elders(db: Session) -> List[User]:
        """社区端：老人档案列表"""
        return db.query(User).filter(User.role == "elder").all()
