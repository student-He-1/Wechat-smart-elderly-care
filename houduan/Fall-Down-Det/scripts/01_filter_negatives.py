# -*- coding: utf-8 -*-
"""过滤未标注图片：剔除可能含跌倒的图，保留安全的负样本（空场景/纯站立），并输出抽查拼图"""
import os, random, collections
from PIL import Image, ImageDraw
from ultralytics import YOLO

ROOT = r'd:\桌面\Fall-Down-Det'
IMG_DIR = os.path.join(ROOT, 'FallDataset', 'img')
TXT_DIR = os.path.join(ROOT, 'FallDataset', 'txt')
OUT_DIR = os.path.join(ROOT, 'neg_check')
os.makedirs(OUT_DIR, exist_ok=True)

# 1. 找出未标注图片
labeled = {os.path.splitext(f)[0] for f in os.listdir(TXT_DIR)}
all_imgs = sorted(os.listdir(IMG_DIR))
unlabeled = [f for f in all_imgs if os.path.splitext(f)[0] not in labeled]
print(f'未标注图片: {len(unlabeled)}')

# 2. 用 COCO 预训练模型检测 person(类0)，按姿态分类
model = YOLO(os.path.join(ROOT, 'yolo26n.pt'))
cats = collections.defaultdict(list)   # empty / standing / fall_like
for idx, f in enumerate(unlabeled):
    path = os.path.join(IMG_DIR, f)
    res = model.predict(path, imgsz=640, conf=0.25, verbose=False)[0]
    with Image.open(path) as im:
        W, H = im.size
    person_boxes = [b for b in res.boxes if int(b.cls[0]) == 0]
    if len(person_boxes) == 0:
        cats['empty'].append(f)
        continue
    lying = False
    for b in person_boxes:
        x1, y1, x2, y2 = b.xyxy[0].tolist()
        h = y2 - y1; w = x2 - x1
        if h / max(w, 1e-6) < 1.2:       # 框不够竖(宽>0.83倍高)即视为疑似躺倒，保守剔除
            lying = True
            break
    cats['fall_like' if lying else 'standing'].append(f)
    if (idx + 1) % 400 == 0:
        print(f'  进度 {idx+1}/{len(unlabeled)}')

for k, v in cats.items():
    print(f'{k}: {len(v)}')
with open(os.path.join(OUT_DIR, 'neg_categories.txt'), 'w', encoding='utf-8') as fp:
    for k, v in cats.items():
        fp.write(f'## {k} {len(v)}\n')
        fp.write('\n'.join(v) + '\n')

# 3. 生成抽查拼图
def montage(files, fname, n=30, cols=6):
    random.seed(1)
    sn = random.sample(files, min(n, len(files)))
    rows = (len(sn) + cols - 1) // cols
    cell = 250
    canvas = Image.new('RGB', (cols * cell, rows * cell), (30, 30, 30))
    d = ImageDraw.Draw(canvas)
    for i, f in enumerate(sn):
        try:
            im = Image.open(os.path.join(IMG_DIR, f)).convert('RGB')
            im.thumbnail((cell - 10, cell - 10))
            x, y = (i % cols) * cell, (i // cols) * cell
            canvas.paste(im, (x + 5, y + 5))
            d.text((x + 5, y + 5), f[:20], fill=(255, 200, 0))
        except Exception as e:
            print('err', f, e)
    canvas.save(os.path.join(OUT_DIR, fname), quality=88)

montage(cats['fall_like'], 'fall_like_sample.jpg')
montage(cats['standing'], 'standing_sample.jpg')
montage(cats['empty'], 'empty_sample.jpg')
print('拼图已保存到', OUT_DIR)