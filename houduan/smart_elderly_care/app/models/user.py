"""用户模型：三端账号与绑定关系"""
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.models.database import Base


class User(Base):
    """用户表（老人 / 子女 / 社区工作人员）"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String(20), nullable=False, index=True)   # elder/daughter/community
    name = Column(String(50), nullable=False)              # 姓名/称呼
    phone = Column(String(20))                             # 手机号
    avatar = Column(String(255))                           # 头像路径（可空）
    # 子女/社区绑定哪位老人（演示家庭里指向老人 user.id）；老人自身为空
    bind_elder_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
