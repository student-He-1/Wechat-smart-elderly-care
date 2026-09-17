"""智慧养老系统主应用"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.config.config import APP_NAME, APP_VERSION, DEBUG
from app.models import Base, engine
from app.routers import api_router
from app.services.reminder_service import reminder_service
from app.services.seed_data import seed_demo_data
from app.services.migrate import run_migrations
from app.services.agent.knowledge_service import KnowledgeService
from app.models.database import SessionLocal
from app.utils.speech import speak
import logging
from fastapi.websockets import WebSocket
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 初始化FastAPI应用
app = FastAPI(
    title=APP_NAME,
    description="AI健康管理与用药提醒后端模块",
    version=APP_VERSION,
    debug=DEBUG
)

# 配置CORS，允许微信小程序访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的小程序域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建数据库表
Base.metadata.create_all(bind=engine)
run_migrations()

# 包含API路由
app.include_router(api_router, prefix="/api")

_STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(os.path.join(_STATIC_DIR, "alerts"), exist_ok=True)
app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")

# WebSocket连接管理
connected_clients = []

@app.websocket("/ws/reminders")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点，用于实时发送提醒信息"""
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        while True:
            # 保持连接
            data = await websocket.receive_text()
            # 可以处理客户端发送的消息
            print(f"Received message: {data}")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        if websocket in connected_clients:
            connected_clients.remove(websocket)

def send_reminder_to_clients(reminder_type: str, message: str, time: str):
    """向所有连接的客户端发送提醒信息
    
    Args:
        reminder_type: 提醒类型
        message: 提醒消息
        time: 提醒时间
    """
    import asyncio
    reminder_data = {
        "type": reminder_type,
        "message": message,
        "time": time
    }
    
    async def send_to_client(client):
        try:
            await client.send_text(json.dumps(reminder_data))
        except Exception as e:
            print(f"Error sending reminder to client: {e}")
            if client in connected_clients:
                connected_clients.remove(client)
    
    for client in connected_clients:
        asyncio.create_task(send_to_client(client))

# 将send_reminder_to_clients函数覆盖到reminder_service模块中
from app.services.reminder_service import reminder_service as reminder_service_instance
# 导入模块
from app.services import reminder_service
# 将函数覆盖到模块中
reminder_service.send_reminder_to_clients = send_reminder_to_clients

# 启动时初始化
@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    logger.info("智慧养老系统API启动成功")
    # 启动提醒服务
    reminder_service_instance.start()
    seed_demo_data()
    # 首次启动构建健康知识库向量（幂等，已构建则跳过；失败不阻断启动）
    try:
        _db = SessionLocal()
        try:
            KnowledgeService.build(_db)
        finally:
            _db.close()
    except Exception as _e:
        logger.warning("知识库构建跳过: %s", _e)
    # 测试语音播报
    # 启动语音播报已移除：语音改由云端合成、小程序端播放，后端本地不发声
    pass

# 关闭时清理
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    # 停止提醒服务
    reminder_service_instance.stop()
    logger.info("智慧养老系统API已关闭")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
