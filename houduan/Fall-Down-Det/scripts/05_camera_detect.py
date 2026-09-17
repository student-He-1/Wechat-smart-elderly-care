# -*- coding: utf-8 -*-
"""
05_camera_detect.py —— 电脑端 USB 摄像头实时跌倒检测
加载训练好的 best.pt，实时画粗红框；连续多帧确认才报警，防止"走路迈步"等单帧误报。

运行环境（务必用 deeplearning 虚拟环境）:
    & "D:\\79458\\Documents\\anaconda3\\envs\\deeplearning\\python.exe" scripts/05_camera_detect.py

常用参数:
    --source 0            摄像头编号(默认0，若有多个摄像头可试 1/2)
    --source video.mp4    也可以直接检测视频文件
    --source photo.jpg    检测单张图片并把结果保存到 runs/camera_alerts/
    --conf 0.4            检测置信度阈值(默认0.4，误报多就调高如0.5，漏报多就调低如0.3)
    --confirm 5 --need 4  最近5帧中至少4帧检出跌倒才报警(防误报核心参数)

画面操作:
    Q 退出 | S 手动抓拍保存
"""
import os, sys, time, argparse
from collections import deque

if os.name == 'nt':
    os.environ.setdefault('KMP_DUPLICATE_LIB_OK', 'TRUE')

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from ultralytics import YOLO

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BEST = os.path.join(ROOT, 'runs', 'train', 'yolo26n_fall', 'weights', 'best.pt')
ALERT_DIR = os.path.join(ROOT, 'runs', 'camera_alerts')
os.makedirs(ALERT_DIR, exist_ok=True)

# ---------- 视觉/报警参数 ----------
RED = (0, 0, 255)          # OpenCV 是 BGR，红=(0,0,255)
RED_RGB = (255, 0, 0)
GREEN = (0, 180, 0)


def get_font(size):
    for fp in [r'C:\Windows\Fonts\msyhbd.ttc', r'C:\Windows\Fonts\msyh.ttc',
               r'C:\Windows\Fonts\simhei.ttf']:
        if os.path.exists(fp):
            return ImageFont.truetype(fp, size)
    return ImageFont.load_default()


def put_text_cn(img_cv2, xy, text, font, color_bgr=(255, 255, 255)):
    """在 OpenCV 图像上绘制中文（PIL 中转），color 为 BGR"""
    pil = Image.fromarray(cv2.cvtColor(img_cv2, cv2.COLOR_BGR2RGB))
    d = ImageDraw.Draw(pil)
    color_rgb = (color_bgr[2], color_bgr[1], color_bgr[0])
    d.text(xy, text, font=font, fill=color_rgb)
    return cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)


def draw_frame(frame, boxes_confs, alarming, fps, conf_th, font_big, font_sm):
    """在帧上画：粗红框+标签、顶部状态条、FPS"""
    h, w = frame.shape[:2]
    lw = max(3, int(min(w, h) / 180))          # 框线粗细随画面自适应
    bar_h = max(46, int(h * 0.07))             # 顶部状态条高度

    # 顶部状态条（先铺底色，检测框与文字后画在上层）
    if alarming:
        frame[:bar_h] = (40, 40, 220)          # BGR 暗红
        state = '!! 跌倒警告 FALL DETECTED !!  已连续确认'
        col = (255, 255, 255)
    else:
        frame[:bar_h] = (30, 30, 30)
        state = '监测中  状态正常'
        col = (0, 230, 0)

    # 检测框（在状态条底色之上）
    for (x1, y1, x2, y2, conf) in boxes_confs:
        cv2.rectangle(frame, (x1, y1), (x2, y2), RED, lw)
        tag = f'FALL {conf:.2f}'
        (tw, th), _ = cv2.getTextSize(tag, cv2.FONT_HERSHEY_DUPLEX, 1.0, 2)
        # 框贴顶部时标签放进框内，避免被状态条遮住
        if y1 - th - 8 < bar_h:
            ly1 = y1 + 4
        else:
            ly1 = y1 - th - 8
        cv2.rectangle(frame, (x1, ly1), (x1 + tw + 10, ly1 + th + 8), RED, -1)
        cv2.putText(frame, tag, (x1 + 5, ly1 + th + 1),
                    cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 255, 255), 2, cv2.LINE_AA)

    frame = put_text_cn(frame, (14, max(6, int(bar_h * 0.18))), state, font_big, col)

    # 左下角运行信息（PIL 绘制，保证中文正常）
    info = f'FPS {fps:4.1f}  |  阈值 conf>={conf_th:.2f}  |  Q退出  S抓拍'
    cv2.rectangle(frame, (0, h - 32), (430, h), (0, 0, 0), -1)
    frame = put_text_cn(frame, (8, h - 28), info, font_sm, (210, 210, 210))
    return frame


def beep_async():
    """非阻塞系统提示音，不卡画面"""
    try:
        import winsound
        winsound.PlaySound('SystemExclamation',
                           winsound.SND_ALIAS | winsound.SND_ASYNC)
    except Exception:
        print('\a', end='', flush=True)


def open_capture(source):
    if str(source).isdigit():
        idx = int(source)
        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)    # Windows 下 DSHOW 更稳
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        if not cap.isOpened():                      # DSHOW 不行就退回默认后端
            cap = cv2.VideoCapture(idx)
        return cap
    cap = cv2.VideoCapture(str(source))
    return cap


def run(model, args):
    cap = open_capture(args.source)
    if not cap.isOpened():
        print(f'[错误] 打不开视频源: {args.source}')
        print('若是摄像头：确认USB摄像头已插好，或尝试 --source 1 / --source 2')
        return 1

    # 连续帧确认逻辑：最近 confirm 帧里有 need 帧检出 -> 报警；连续 clear 帧无检出 -> 解除
    recent = deque(maxlen=args.confirm)
    alarming = False
    clear_streak = 0
    last_beep = 0.0
    last_save = 0.0
    f_prev = time.time()
    fps = 0.0

    font_big = get_font(26)
    font_sm = get_font(18)
    print('检测已启动，按 Q 退出。报警抓拍自动保存到:', ALERT_DIR)

    while True:
        ok, frame = cap.read()
        if not ok:
            print('视频流结束或读取失败')
            break

        # 推理（GPU）
        results = model.predict(frame, imgsz=640, conf=args.conf, verbose=False)[0]
        det = []
        if results.boxes is not None:
            for b in results.boxes:
                x1, y1, x2, y2 = map(int, b.xyxy[0].tolist())
                det.append((x1, y1, x2, y2, float(b.conf[0])))

        hit = 1 if det else 0
        recent.append(hit)
        if len(recent) == recent.maxlen and sum(recent) >= args.need and not alarming:
            alarming = True
            beep_async()
        if hit == 0:
            clear_streak += 1
        else:
            clear_streak = 0
        if alarming and clear_streak >= args.clear:
            alarming = False

        # 报警瞬间自动抓拍（节流 3 秒，避免刷屏）
        now = time.time()
        if alarming and det and now - last_save > 3.0:
            fp = os.path.join(ALERT_DIR, f'fall_{time.strftime("%Y%m%d_%H%M%S")}.jpg')
            saved = draw_frame(frame.copy(), det, alarming, fps, args.conf, font_big, font_sm)
            cv2.imwrite(fp, saved)
            print(f'[报警] 检测到跌倒，已抓拍: {fp}')
            last_save = now
        if alarming and now - last_beep > 2.0:
            beep_async()
            last_beep = now

        fps = 0.85 * fps + 0.15 * (1.0 / max(now - f_prev, 1e-6))
        f_prev = now
        view = draw_frame(frame, det, alarming, fps, args.conf, font_big, font_sm)
        cv2.imshow('Fall Detection (Q quit / S snapshot)', view)

        key = cv2.waitKey(1) & 0xFF
        if key in (ord('q'), ord('Q')):
            break
        if key in (ord('s'), ord('S')):
            fp = os.path.join(ALERT_DIR, f'snap_{time.strftime("%Y%m%d_%H%M%S")}.jpg')
            cv2.imwrite(fp, view)
            print('手动抓拍:', fp)

    cap.release()
    cv2.destroyAllWindows()
    print('已退出。抓拍/报警图片目录:', ALERT_DIR)
    return 0


def run_image(model, args):
    """单张图片模式：无窗口也能跑，结果固定保存到 runs/camera_alerts/"""
    frame = cv2.imread(args.source)
    if frame is None:
        print('[错误] 读不到图片:', args.source)
        return 1
    results = model.predict(frame, imgsz=640, conf=args.conf, verbose=False)[0]
    det = []
    if results.boxes is not None:
        for b in results.boxes:
            x1, y1, x2, y2 = map(int, b.xyxy[0].tolist())
            det.append((x1, y1, x2, y2, float(b.conf[0])))
    view = draw_frame(frame, det, bool(det), 0.0, args.conf, get_font(26), get_font(18))
    out = os.path.join(ALERT_DIR, 'pred_' + os.path.basename(args.source))
    cv2.imwrite(out, view)
    print(f'检出跌倒框 {len(det)} 个，结果已保存: {out}')
    return 0


def main():
    ap = argparse.ArgumentParser(description='USB摄像头实时跌倒检测')
    ap.add_argument('--source', default='0', help='0=摄像头(默认)，也可传视频/图片路径')
    ap.add_argument('--weights', default=BEST)
    ap.add_argument('--conf', type=float, default=0.4)
    ap.add_argument('--confirm', type=int, default=5, help='确认窗口帧数')
    ap.add_argument('--need', type=int, default=4, help='窗口内至少检出几帧才报警')
    ap.add_argument('--clear', type=int, default=15, help='连续多少帧无检出解除报警')
    args = ap.parse_args()

    if not os.path.exists(args.weights):
        print('[错误] 找不到模型权重:', args.weights)
        return 1
    print('加载模型:', args.weights)
    model = YOLO(args.weights)

    if os.path.isfile(args.source) and args.source.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
        return run_image(model, args)
    return run(model, args)


if __name__ == '__main__':
    sys.exit(main())