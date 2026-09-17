"""用户路由：演示登录/切换身份、查询"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.models.database import get_db
from app.models.user import User
from app.schemas.user import UserLogin, UserResponse
from app.services.user_service import UserService

router = APIRouter()


@router.post("/login", response_model=UserResponse, summary="演示登录/切换身份")
def login(payload: UserLogin, db: Session = Depends(get_db)):
    try:
        return UserService.login_or_create(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/me", response_model=UserResponse, summary="按 id 获取当前用户")
def me(user_id: int, db: Session = Depends(get_db)):
    user = UserService.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.get("/elders", summary="社区端：老人档案列表")
def elders(db: Session = Depends(get_db)):
    items = UserService.list_elders(db)
    return {"message": "success", "data": [UserResponse.model_validate(u).model_dump() for u in items]}


@router.get("", summary="按角色列用户")
def list_users(role: Optional[str] = None, db: Session = Depends(get_db)):
    if role:
        items = UserService.list_by_role(db, role)
    else:
        items = db.query(User).all()
    return {"message": "success",
            "data": [UserResponse.model_validate(u).model_dump() for u in items]}
