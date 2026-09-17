# -*- coding: utf-8 -*-
"""
04_evaluate.py —— 跌倒检测模型最终评估与可视化
1) 用 best.pt 在独立 test 集（训练/调参全程未见过的 457 张）上评估 mAP/P/R
2) 输出 test 集逐图预测可视化拼图（大框、粗线、醒目配色，便于看清跌倒检出）
3) 支持对任意图片/文件夹做实景推理：--source <图片或目录或视频>

用法:
    python scripts/04_evaluate.py                       # test集评估 + 预测拼图
    python scripts/04_evaluate.py --source xxx.jpg     # 单张实景图推理
    python scripts/04_evaluate.py --source some_dir    # 目录批量推理
"""
import os, sys, glob, random, argparse
if os.name == 'nt':
    os.environ.setdefault('KMP_DUPLICATE_LIB_OK', 'TRUE')

from ultralytics import YOLO
from PIL import Image, ImageDraw, ImageFont

ROOT = r'd:\桌面\Fall-Down-Det'
BEST = os.path.join(ROOT, 'runs', 'train', 'yolo26n_fall', 'weights', 'best.pt')
DATA = os.path.join(ROOT, 'FallDataset-yolo', 'data.yaml')
TEST_IMG = os.path.join(ROOT, 'FallDataset-yolo', 'images', 'test')
OUT = os.path.join(ROOT, 'runs', 'eval_test')

# 醒目配色（老人/演示场景偏好大框高对比）
FALL_COLOR = (255, 0, 0)      # 警示红框 (RGB)
LINE_W = 5                    # 粗框线
CONF_TH = 0.35


def load_font(size):
    for fp in [r'C:\Windows\Fonts\msyhbd.ttc', r'C:\Windows\Fonts\msyh.ttc',
               r'C:\Windows\Fonts\simhei.ttf', r'C:\Windows\Fonts\arialbd.ttf']:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                pass
    return ImageFont.load_default()


def draw_predictions(img_path, result):
    """在 PIL 图上画大框+中文标签，返回标注后图像"""
    im = Image.open(img_path).convert('RGB')
    d = ImageDraw.Draw(im)
    W, H = im.size
    lw = max(LINE_W, int(min(W, H) / 120))      # 按图大小自适应粗线
    fs = max(20, int(min(W, H) / 22))
    font = load_font(fs)
    n = 0
    if result.boxes is not None:
        for b in result.boxes:
            x1, y1, x2, y2 = map(int, b.xyxy[0].tolist())
            conf = float(b.conf[0])
            d.rectangle([x1, y1, x2, y2], outline=FALL_COLOR, width=lw)
            tag = f'FALL {conf:.2f}'
            tb = d.textbbox((x1, y1 - fs - 6), tag, font=font)
            d.rectangle(tb, fill=FALL_COLOR)
            d.text((x1, y1 - fs - 6), tag, fill=(255, 255, 255), font=font)
            n += 1
    return im, n


def make_grid(images, cols=3, cell=560):
    rows = (len(images) + cols - 1) // cols
    canvas = Image.new('RGB', (cols * cell, rows * cell), (24, 24, 24))
    for i, im in enumerate(images):
        im.thumbnail((cell - 12, cell - 12))
        x, y = (i % cols) * cell, (i // cols) * cell
        canvas.paste(im, (x + 6, y + 6))
    return canvas


def evaluate_test():
    os.makedirs(OUT, exist_ok=True)
    model = YOLO(BEST)
    # 1) 正式指标（独立 test 集）
    metrics = model.val(data=DATA, split='test', batch=16, imgsz=640,
                        project=os.path.join(ROOT, 'runs'), name='eval_test_raw',
                        exist_ok=True)
    print('\n========== 独立 TEST 集最终评估 ==========')
    print(f'Precision : {metrics.box.mp:.4f}')
    print(f'Recall    : {metrics.box.mr:.4f}')
    print(f'mAP50     : {metrics.box.map50:.4f}')
    print(f'mAP50-95  : {metrics.box.map:.4f}')

    # 2) 预测可视化：随机抽 12 张 test 图（其中保证有检出、无检出各占一定比例）
    test_imgs = sorted(glob.glob(os.path.join(TEST_IMG, '*.jpg')))
    random.seed(7)
    sample = random.sample(test_imgs, min(24, len(test_imgs)))
    results = model.predict(sample, imgsz=640, conf=CONF_TH, verbose=False)
    with_det, no_det = [], []
    for p, r in zip(sample, results):
        im, n = draw_predictions(p, r)
        (with_det if n > 0 else no_det).append(im)
    picked = (with_det[:9] + no_det[:3]) if len(with_det) >= 9 else with_det + no_det
    picked = picked[:12]
    if picked:
        grid = make_grid(picked, cols=3)
        gp = os.path.join(OUT, 'test_predictions_grid.jpg')
        grid.save(gp, quality=90)
        print(f'预测拼图(有检出{min(9,len(with_det))}张+无检出{max(0,12-min(9,len(with_det)))}张): {gp}')
    print(f'详细曲线/混淆矩阵见: {os.path.join(ROOT, "runs", "eval_test_raw")}')


def infer_source(src):
    model = YOLO(BEST)
    if os.path.isdir(src):
        files = sorted(glob.glob(os.path.join(src, '*.jpg')) +
                       glob.glob(os.path.join(src, '*.png')) + glob.glob(os.path.join(src, '*.jpeg')))
    elif os.path.isfile(src):
        files = [src]
    else:
        raise FileNotFoundError(src)
    out_dir = os.path.join(ROOT, 'runs', 'infer_custom')
    os.makedirs(out_dir, exist_ok=True)
    results = model.predict(files, imgsz=640, conf=CONF_TH, verbose=False, save=False)
    images = []
    fall_cnt = 0
    for p, r in zip(files, results):
        im, n = draw_predictions(p, r)
        name = 'pred_' + os.path.basename(p)
        im.save(os.path.join(out_dir, name), quality=90)
        images.append(im)
        fall_cnt += n
        print(f'{os.path.basename(p)}: 检出跌倒框 {n} 个')
    if len(images) > 1:
        grid = make_grid(images[:12], cols=3)
        grid.save(os.path.join(out_dir, 'infer_grid.jpg'), quality=90)
    print(f'\n实景推理完成，共检出 {fall_cnt} 个跌倒框，结果目录: {out_dir}')


def hardcase_test(n_sample=18):
    """用过滤阶段剔除的 fall_like 桶(172张，训练完全未见过)做泛化/误报测试。
    该桶混合真跌倒/蹲坐/军警/事故，是最贴近真实的困难样本。"""
    src_img = os.path.join(ROOT, 'FallDataset', 'img')
    names, sec = [], None
    for line in open(os.path.join(ROOT, 'neg_check', 'neg_categories.txt'), encoding='utf-8'):
        line = line.rstrip('\n')
        if line.startswith('##'):
            sec = line.split(' ')[1]; continue
        if line and sec == 'fall_like':
            names.append(line)
    files = [os.path.join(src_img, f) for f in names if os.path.exists(os.path.join(src_img, f))]
    random.seed(11)
    sample = random.sample(files, min(n_sample, len(files)))
    model = YOLO(BEST)
    results = model.predict(sample, imgsz=640, conf=CONF_TH, verbose=False)
    hit = sum(1 for r in results if r.boxes is not None and len(r.boxes) > 0)
    images = []
    for p, r in zip(sample, results):
        im, _ = draw_predictions(p, r)
        images.append(im)
    out_dir = os.path.join(ROOT, 'runs', 'eval_test')
    os.makedirs(out_dir, exist_ok=True)
    grid = make_grid(images, cols=3)
    gp = os.path.join(out_dir, 'hardcase_generalization.jpg')
    grid.save(gp, quality=90)
    print(f'困难场景 {len(sample)} 张中报跌倒 {hit} 张（该桶真跌倒/非跌倒混合，需人工核对红框是否合理）')
    print('困难场景拼图:', gp)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', default='', help='图片/文件夹/视频路径；留空则评估 test 集')
    ap.add_argument('--hardcase', action='store_true', help='用未训练的172张困难场景图做泛化/误报测试')
    a = ap.parse_args()
    if a.source:
        infer_source(a.source)
    elif a.hardcase:
        hardcase_test()
    else:
        evaluate_test()