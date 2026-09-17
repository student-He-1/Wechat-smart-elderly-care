"""API路由模块"""
from fastapi import APIRouter
from .medicine import router as medicine_router
from .health import router as health_router
from .test import router as test_router
from .tts import router as tts_router
from .asr import router as asr_router
from .users import router as users_router
from .messages import router as messages_router
from .alerts import router as alerts_router
from .medicine_log import router as medicine_log_router
from .orders import router as orders_router
from .health_agent import router as health_agent_router
from .companion import router as companion_router

# 创建主路由
api_router = APIRouter()

# 包含子路由
api_router.include_router(medicine_router, prefix="/medicine", tags=["medicine"])
api_router.include_router(health_router, prefix="/health", tags=["health"])
api_router.include_router(test_router, prefix="/test", tags=["test"])
api_router.include_router(tts_router, prefix="/tts", tags=["tts"])
api_router.include_router(asr_router, prefix="/asr", tags=["asr"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(messages_router, prefix="/messages", tags=["messages"])
api_router.include_router(alerts_router, prefix="/alerts", tags=["alerts"])
api_router.include_router(medicine_log_router, prefix="/medicine-log", tags=["medicine-log"])
api_router.include_router(orders_router, prefix="/orders", tags=["orders"])
api_router.include_router(health_agent_router, prefix="/health-agent", tags=["health-agent"])
api_router.include_router(companion_router, prefix="/companion", tags=["companion"])
