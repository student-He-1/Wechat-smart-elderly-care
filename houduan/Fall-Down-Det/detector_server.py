# -*- coding: utf-8 -*-
"""
跌倒检测 + 视频推流服务（独立运行，使用 deeplearning 环境）
- 后台线程：USB 摄像头抓帧 -> YOLO(best.pt) 推理 -> 连续帧确认 -> 画框 -> JPEG
- WebSocket /ws/stream：把最新 JPEG 帧以二进制推给前端（约 12~15fps），
  每 ~1 秒插一条文本 JSON 状态帧 {type:'status', fall, fps}
- 跌倒确认瞬间 POST 主后端 /api/alerts(type=fall)，落库 + WS 推子女/社区（复用现有链路）
运行：  D:\\79458\\Documents\\anaconda3\\envs\\deeplearning\\python.exe detector_server.py
"""
import threading
import time
import asyncio
import os
from collections import deque

import cv2
import requests
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from ultralytics import YOLO

# ============ 配置 ============
MODEL_PATH = r"D:\桌面\houduan\Fall-Down-Det\runs\train\yolo26n_fall\weights\best.pt"
CAM_INDEX = int(os.environ.get("CAM_INDEX", "1"))  # USB 摄像头；换设备改这里或设环境变量
CONF = 0.4                    # 检测置信度
CONFIRM_WIN = 5               # 确认窗口帧数
CONFIRM_NEED = 4              # 窗口内至少几帧检出跌倒才报警
CLEAR_NEED = 5                # 报警中连续几帧无检出则解除
TARGET_FPS = 15               # 推流目标帧率
JPEG_QUALITY = 62             # JPEG 质量（局域网流畅优先）
FRAME_W = 640
MAIN_ALERT_API = "http://localhost:8000/api/alerts"
ELDER_ID = 1
ALERT_COOLDOWN = 120.0        # 报警后多少秒内，即使再次误判/重复跌倒也静默不上报、不截图
PORT = 5002

RED = (40, 40, 220)           # BGR
DARK = (30, 30, 30)

# ============ 全局状态 ============
model = YOLO(MODEL_PATH)
cap = cv2.VideoCapture(CAM_INDEX, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_W)

_state = {"jpeg": b"", "fall": False, "fps": 0.0, "seq": 0}
_lock = threading.Lock()


def draw(frame, boxes, alarming, fps):
    h, w = frame.shape[:2]
    bar_h = 34
    frame[:bar_h] = RED if alarming else DARK
    state_txt = "!! FALL DETECTED !!" if alarming else "MONITORING"
    cv2.putText(frame, state_txt, (10, 24), cv2.FONT_HERSHEY_SIMPLEX,
                0.7, (255, 255, 255), 2)
    for (x1, y1, x2, y2, c) in boxes:
        cv2.rectangle(frame, (x1, y1), (x2, y2), RED, 2)
        tag = f"FALL {c:.2f}"
        cv2.rectangle(frame, (x1, max(0, y1 - 22)), (x1 + 110, y1), RED, -1)
        cv2.putText(frame, tag, (x1 + 4, y1 - 6), cv2.FONT_HERSHEY_SIMPLEX,
                    0.55, (255, 255, 255), 1)
    cv2.rectangle(frame, (0, h - 26), (300, h), (0, 0, 0), -1)
    cv2.putText(frame, f"FPS {fps:4.1f}  conf>={CONF:.2f}", (8, h - 8),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (210, 210, 210), 1)
    return frame


def post_alert(snapshot_b64=None):
    try:
        body = {
            "elder_id": ELDER_ID,
            "type": "fall",
            "level": "urgent",
            "detail": "摄像头检测到老人跌倒，请立即查看"
        }
        if snapshot_b64:
            body["snapshot"] = "data:image/jpeg;base64," + snapshot_b64
        requests.post(MAIN_ALERT_API, json=body, timeout=5)
        print("[ALERT] 已上报跌倒到主后端（含现场截图)" if snapshot_b64 else "[ALERT] 已上报跌倒")
    except Exception as e:
        print("[ALERT] 上报失败(不影响推流):", e)


def capture_loop():
    recent = deque(maxlen=CONFIRM_WIN)
    alarming = False
    clear_cnt = 0
    last_alert_time = 0.0
    while True:
        t0 = time.time()
        ok, frame = cap.read()
        if not ok:
            time.sleep(0.05)
            continue
        results = model.predict(frame, imgsz=640, conf=CONF, verbose=False)[0]
        boxes, hit = [], False
        for b in results.boxes:
            x1, y1, x2, y2 = map(int, b.xyxy[0])
            c = float(b.conf[0])
            boxes.append((x1, y1, x2, y2, c))
            if int(b.cls[0]) == 0:
                hit = True
        recent.append(1 if hit else 0)

        new_fall = False
        if not alarming and sum(recent) >= CONFIRM_NEED:
            # 每次「新进入」跌倒状态只报一次；连续 CLEAR_NEED 帧无检出解除后，再次跌倒才会再报
            alarming = True
            new_fall = True
        elif alarming:
            clear_cnt = clear_cnt + 1 if not hit else 0
            if clear_cnt >= CLEAR_NEED:
                alarming = False
                clear_cnt = 0

        fps = 1.0 / max(time.time() - t0, 1e-6)
        view = draw(frame, boxes, alarming, fps)
        ok2, buf = cv2.imencode(".jpg", view, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
        if ok2:
            jpg = buf.tobytes()
            with _lock:
                _state["jpeg"] = jpg
                _state["fall"] = alarming
                _state["fps"] = fps
                _state["seq"] += 1
            if new_fall:
                # 冷却期内（报警后 ALERT_COOLDOWN 秒内）即使再次跌倒/误判，也静默不报不截图，防止刷屏
                now = time.time()
                if now - last_alert_time >= ALERT_COOLDOWN:
                    last_alert_time = now
                    # 跌倒现场帧：上报主后端存档 + 本地留一份（带时间戳）
                    import base64
                    b64 = base64.b64encode(jpg).decode("ascii")
                    post_alert(b64)
                    shot_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alert_shots")
                    os.makedirs(shot_dir, exist_ok=True)
                    buf.tofile(os.path.join(shot_dir, f"fall_{time.strftime('%Y%m%d_%H%M%S')}.jpg"))
                else:
                    print("[ALERT] 冷却期内，静默不重复上报")
        # 不主动 sleep：cap.read() 会按摄像头硬件帧率阻塞，自动适配 10/30fps


app = FastAPI()


@app.on_event("startup")
def _start():
    t = threading.Thread(target=capture_loop, daemon=True)
    t.start()
    print(f"[detector] 采集线程已启动，推流 ws://0.0.0.0:{PORT}/ws/stream")


@app.websocket("/ws/stream")
async def ws_stream(ws: WebSocket):
    await ws.accept()
    print("[ws] 前端已连接监控流")
    last_seq = -1
    last_status_ts = 0.0
    try:
        while True:
            with _lock:
                jpg = _state["jpeg"]
                fall = _state["fall"]
                fps = _state["fps"]
                seq = _state["seq"]
            # 只有采集到新帧才推送，不重复发同一帧；帧率自动跟随摄像头硬件
            if jpg and seq != last_seq:
                last_seq = seq
                await ws.send_bytes(jpg)
                now = asyncio.get_event_loop().time()
                if now - last_status_ts >= 1.0:  # 约每秒一条状态
                    last_status_ts = now
                    await ws.send_json({"type": "status", "fall": fall, "fps": round(fps, 1)})
            await asyncio.sleep(1.0 / 30.0)
    except WebSocketDisconnect:
        print("[ws] 前端断开")


@app.get("/status")
def status():
    with _lock:
        return {"fall": _state["fall"], "fps": round(_state["fps"], 1)}


@app.get("/latest.jpg")
def latest():
    with _lock:
        return Response(content=_state["jpeg"], media_type="image/jpeg")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="warning")
