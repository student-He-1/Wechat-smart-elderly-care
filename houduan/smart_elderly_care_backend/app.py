from flask import Flask, request, jsonify
from flask_cors import CORS
import time
import datetime
import sqlite3
import threading
import random

# 尝试导入OpenCV，如果失败则使用模拟数据
try:
    import cv2
    import base64
    has_opencv = True
except ImportError:
    has_opencv = False

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 数据库初始化
def init_db():
    conn = sqlite3.connect('elderly_care.db')
    c = conn.cursor()
    # 创建用户表
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT,
                  phone TEXT,
                  emergency_contacts TEXT)''')
    # 创建监控记录表
    c.execute('''CREATE TABLE IF NOT EXISTS monitor_records
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  timestamp TEXT,
                  status TEXT,
                  event_type TEXT,
                  description TEXT)''')
    # 创建预警表
    c.execute('''CREATE TABLE IF NOT EXISTS alerts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  timestamp TEXT,
                  alert_level TEXT,
                  message TEXT,
                  is_handled INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

init_db()

# 全局状态变量，用于保持检测结果的连续性
last_activity = '活动'  # 上次活动状态
fall_detected = False  # 跌倒状态
fall_duration = 0  # 跌倒持续时间

# 模拟跌倒检测模型
def detect_fall(frame):
    global fall_detected, fall_duration
    
    # 这里使用简单的模拟实现，实际项目中应使用真实的计算机视觉模型
    # 例如使用OpenCV的人体姿态估计或深度学习模型
    
    # 如果已经检测到跌倒，保持一段时间的跌倒状态
    if fall_detected:
        fall_duration += 1
        # 跌倒状态持续5秒
        if fall_duration >= 5:
            fall_detected = False
            fall_duration = 0
        return True
    
    # 1%的概率检测到跌倒（降低误报率）
    if random.random() < 0.01:
        fall_detected = True
        fall_duration = 0
        return True
    
    return False

# 模拟活动监测
def detect_activity(frame):
    global last_activity
    
    # 模拟活动监测
    activities = ['静止', '活动', '睡眠']
    
    # 70%的概率保持上次状态，30%的概率切换状态
    if random.random() < 0.7:
        return last_activity
    else:
        # 从其他状态中随机选择一个
        other_activities = [activity for activity in activities if activity != last_activity]
        new_activity = random.choice(other_activities)
        last_activity = new_activity
        return new_activity

# 监控线程
def monitor_thread():
    while True:
        # 模拟监控过程
        time.sleep(3)  # 每3秒检查一次，与前端保持一致
        
        # 模拟获取视频帧
        # 实际项目中应从摄像头获取
        frame = None
        
        # 检测跌倒
        is_fall = detect_fall(frame)
        # 检测活动
        activity = detect_activity(frame)
        
        # 处理检测结果
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn = sqlite3.connect('elderly_care.db')
        c = conn.cursor()
        
        if is_fall:
            # 红色预警
            c.execute("INSERT INTO alerts (user_id, timestamp, alert_level, message) VALUES (?, ?, ?, ?)",
                     (1, current_time, 'red', '检测到老人跌倒！'))
            c.execute("INSERT INTO monitor_records (user_id, timestamp, status, event_type, description) VALUES (?, ?, ?, ?, ?)",
                     (1, current_time, '异常', '跌倒', '检测到老人跌倒'))
        else:
            # 正常状态
            c.execute("INSERT INTO monitor_records (user_id, timestamp, status, event_type, description) VALUES (?, ?, ?, ?, ?)",
                     (1, current_time, '正常', '活动', f'老人{activity}状态'))
        
        conn.commit()
        conn.close()

# 启动监控线程
monitor_thread_instance = threading.Thread(target=monitor_thread)
monitor_thread_instance.daemon = True
monitor_thread_instance.start()

# API接口

@app.route('/', methods=['GET'])
def index():
    return jsonify({'message': 'Smart Elderly Care Backend API'})

@app.route('/api/monitor/status', methods=['GET'])
def get_monitor_status():
    """获取监控状态"""
    conn = sqlite3.connect('elderly_care.db')
    c = conn.cursor()
    
    # 获取最新的监控记录
    c.execute("SELECT timestamp, status, event_type, description FROM monitor_records ORDER BY timestamp DESC LIMIT 1")
    record = c.fetchone()
    
    if record:
        timestamp, status, event_type, description = record
        status_data = {
            'currentTime': timestamp,
            'status': status,
            'eventType': event_type,
            'description': description,
            'roomStatus': '有人'  # 模拟房间状态
        }
    else:
        status_data = {
            'currentTime': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': '正常',
            'eventType': '活动',
            'description': '老人正常活动',
            'roomStatus': '有人'
        }
    
    conn.close()
    return jsonify(status_data)

@app.route('/api/monitor/history', methods=['GET'])
def get_monitor_history():
    """获取历史记录"""
    conn = sqlite3.connect('elderly_care.db')
    c = conn.cursor()
    
    # 获取最近的10条记录
    c.execute("SELECT timestamp, event_type, description FROM monitor_records ORDER BY timestamp DESC LIMIT 10")
    records = c.fetchall()
    
    history = []
    for record in records:
        timestamp, event_type, description = record
        history.append({
            'time': timestamp,
            'event': event_type,
            'desc': description
        })
    
    conn.close()
    return jsonify(history)

@app.route('/api/monitor/alerts', methods=['GET'])
def get_alerts():
    """获取预警信息"""
    conn = sqlite3.connect('elderly_care.db')
    c = conn.cursor()
    
    # 获取未处理的预警
    c.execute("SELECT id, timestamp, alert_level, message FROM alerts WHERE is_handled = 0 ORDER BY timestamp DESC")
    alerts = c.fetchall()
    
    alert_list = []
    for alert in alerts:
        alert_id, timestamp, alert_level, message = alert
        alert_list.append({
            'id': alert_id,
            'timestamp': timestamp,
            'level': alert_level,
            'message': message
        })
    
    conn.close()
    return jsonify(alert_list)

@app.route('/api/monitor/alert/handle', methods=['POST'])
def handle_alert():
    """处理预警"""
    data = request.get_json()
    alert_id = data.get('id')
    
    if not alert_id:
        return jsonify({'error': '缺少预警ID'}), 400
    
    conn = sqlite3.connect('elderly_care.db')
    c = conn.cursor()
    c.execute("UPDATE alerts SET is_handled = 1 WHERE id = ?", (alert_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': '预警已处理'})

@app.route('/api/emergency/help', methods=['POST'])
def emergency_help():
    """紧急求助"""
    data = request.get_json()
    user_id = data.get('userId', 1)
    
    # 模拟发送紧急消息给联系人
    # 实际项目中应集成短信服务或其他通知方式
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 记录紧急求助
    conn = sqlite3.connect('elderly_care.db')
    c = conn.cursor()
    c.execute("INSERT INTO alerts (user_id, timestamp, alert_level, message) VALUES (?, ?, ?, ?)",
             (user_id, current_time, 'red', '老人请求紧急帮助！'))
    c.execute("INSERT INTO monitor_records (user_id, timestamp, status, event_type, description) VALUES (?, ?, ?, ?, ?)",
             (user_id, current_time, '异常', '紧急求助', '老人请求紧急帮助'))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': '紧急求助已发送', 'timestamp': current_time})

# 全局摄像头对象
cap = None

# 初始化摄像头
def init_camera():
    global cap
    if has_opencv and cap is None:
        try:
            cap = cv2.VideoCapture(0)
            print("摄像头初始化成功")
        except Exception as e:
            print(f"摄像头初始化失败: {e}")

# 关闭摄像头
def close_camera():
    global cap
    if cap is not None:
        cap.release()
        cap = None
        print("摄像头已关闭")

# 初始化摄像头
init_camera()

@app.route('/api/monitor/stream', methods=['GET'])
def get_monitor_stream():
    """获取监控流数据"""
    # 获取当前时间
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 尝试使用摄像头捕获实时画面
    frame = None
    if has_opencv and cap is not None:
        try:
            # 从已打开的摄像头中读取帧
            ret, frame = cap.read()
            
            if ret:
                # 进一步减小图像大小，减少传输数据量
                resized_frame = cv2.resize(frame, (240, 180))
                # 进一步压缩图像质量
                _, buffer = cv2.imencode('.jpg', resized_frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
                frame_base64 = base64.b64encode(buffer).decode('utf-8')
                frame_url = f'data:image/jpeg;base64,{frame_base64}'
            else:
                # 如果无法获取摄像头，使用默认图像
                frame_url = 'https://picsum.photos/240/180?random=1'
        except Exception as e:
            # 如果摄像头读取失败，使用默认图像
            print(f"摄像头读取失败: {e}")
            frame_url = 'https://picsum.photos/320/240?random=1'
    else:
        # 如果没有OpenCV或摄像头未初始化，使用默认图像
        frame_url = 'https://picsum.photos/320/240?random=1'
    
    # 使用检测算法获取状态
    is_fall = detect_fall(frame)
    activity = detect_activity(frame)
    
    # 根据检测结果确定状态
    if is_fall:
        status = '异常'
    else:
        status = '正常'
    
    # 构建返回数据
    stream_data = {
        'timestamp': current_time,
        'status': status,
        'activity': activity,
        'frame': frame_url
    }
    
    return jsonify(stream_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)