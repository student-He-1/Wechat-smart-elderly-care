# -*- coding: utf-8 -*-
"""
02_build_dataset.py  —— 数据划分器
将原始 FallDataset（4576 张跌倒标注 + 已过滤负样本）整理为标准 YOLO 数据集：
    FallDataset-yolo/
        images/train  images/val  images/test
        labels/train  labels/val  labels/test
        data.yaml                 (nc=1, names=['fall'])
划分：标注图 80% train / 10% val / 10% test（固定种子，可复现）
负样本（站立场景 494 + 空场景 498 = 992 张，仅作背景图）全部放入 train，标签为空文件。
txt 中类别 id 1 统一归一化为 0。

用法：python scripts/02_build_dataset.py
"""
import os, random, shutil, sys
from collections import Counter

ROOT = r'd:\桌面\Fall-Down-Det'
SRC_IMG = os.path.join(ROOT, 'FallDataset', 'img')
SRC_TXT = os.path.join(ROOT, 'FallDataset', 'txt')
NEG_LIST = os.path.join(ROOT, 'neg_check', 'neg_categories.txt')   # 负样本名单(过滤脚本产物)
OUT = os.path.join(ROOT, 'FallDataset-yolo')

SEED = 42
RATIO = (0.8, 0.1, 0.1)   # train/val/test
NEG_SPLIT = 0.0           # 负样本进 val 的比例(0=全部进 train，避免 val 出现无标签图警告)


def read_negatives():
    """读取过滤脚本产出的负样本名单: 返回 (standing+empty 的可用名单, 排除的 fall_like)"""
    ok, excluded = [], []
    sec = None
    for line in open(NEG_LIST, encoding='utf-8'):
        line = line.rstrip('\n')
        if line.startswith('##'):
            sec = line.split(' ')[1]
            continue
        if not line:
            continue
        (excluded if sec == 'fall_like' else ok).append(line)
    return ok, excluded


def parse_txt(path, tol=1.5):
    """解析 txt 标注 -> [(cls, cx, cy, w, h)...]。
    cls 1 归一化为 0；框略超出图像([0,1])时做边界裁剪，严重越界(>tol 倍)才判为异常。"""
    boxes = []
    with open(path, encoding='utf-8', errors='ignore') as fp:
        for ln in fp:
            parts = ln.split()
            if len(parts) != 5:
                return None, f'字段数异常: {ln.strip()}'
            try:
                cls, cx, cy, w, h = map(float, parts)
            except ValueError:
                return None, f'坐标非数字: {ln.strip()}'
            cls = 0 if int(cls) == 1 else int(cls)
            # 转像素框再裁剪回 [0,1]
            x1, y1 = cx - w / 2, cy - h / 2
            x2, y2 = cx + w / 2, cy + h / 2
            if not (-tol < x1 < tol and -tol < y1 < tol and -tol < x2 < tol and -tol < y2 < tol):
                return None, f'框严重越界: {ln.strip()}'
            x1, y1 = max(0.0, x1), max(0.0, y1)
            x2, y2 = min(1.0, x2), min(1.0, y2)
            w, h = x2 - x1, y2 - y1
            if w <= 1e-6 or h <= 1e-6:
                return None, f'裁剪后为空框: {ln.strip()}'
            boxes.append((cls, (x1 + x2) / 2, (y1 + y2) / 2, w, h))
    return boxes, None


def link_or_copy(src, dst):
    try:
        os.link(src, dst)            # NTFS 硬链接，省空间省时间
    except OSError:
        shutil.copy2(src, dst)


def main():
    random.seed(SEED)
    if os.path.exists(OUT):          # 重建前清空旧输出
        shutil.rmtree(OUT)
        print(f'已清空旧输出: {OUT}')

    # 1. 收集标注图（txt 与 img 一一对应）
    labeled = []
    problems = []
    for f in sorted(os.listdir(SRC_TXT)):
        stem = os.path.splitext(f)[0]
        img = os.path.join(SRC_IMG, stem + '.jpg')
        if not os.path.exists(img):
            problems.append(f'缺图: {stem}')
            continue
        boxes, err = parse_txt(os.path.join(SRC_TXT, f))
        if err or not boxes:
            problems.append(f'{stem}: {err or "空标注"}')
            continue
        labeled.append((stem, boxes))
    print(f'有效标注图: {len(labeled)}  异常: {len(problems)}')
    for p in problems[:20]:
        print('  !', p)

    cls_counter = Counter(c for _, boxes in labeled for c, *_ in boxes)
    print('类别分布(归一化后):', dict(cls_counter))

    # 2. 负样本名单
    negs, fall_like = read_negatives()
    print(f'负样本可用: {len(negs)}  过滤剔除(疑似跌倒): {len(fall_like)}')
    # 负样本同样要求图片存在
    neg_ok = [n for n in negs if os.path.exists(os.path.join(SRC_IMG, n))]
    print(f'负样本图片校验通过: {len(neg_ok)}')

    # 3. 划分
    random.shuffle(labeled)
    n = len(labeled)
    n_val = int(n * RATIO[1]); n_test = int(n * RATIO[2])
    n_train = n - n_val - n_test
    split = {'train': labeled[:n_train], 'val': labeled[n_train:n_train + n_val],
             'test': labeled[n_train + n_val:] }

    # 负样本：默认全部进 train，可留 unlabel_ratio 进 val
    n_neg_val = int(len(neg_ok) * NEG_SPLIT)
    random.shuffle(neg_ok)
    neg_all = {'train': neg_ok[n_neg_val:], 'val': neg_ok[:n_neg_val]}

    # 4. 落盘
    for part in ('train', 'val', 'test'):
        os.makedirs(os.path.join(OUT, 'images', part), exist_ok=True)
        os.makedirs(os.path.join(OUT, 'labels', part), exist_ok=True)
    empty_count = 0
    for part, items in split.items():
        for stem, boxes in items:
            src_img = os.path.join(SRC_IMG, stem + '.jpg')
            link_or_copy(src_img, os.path.join(OUT, 'images', part, stem + '.jpg'))
            with open(os.path.join(OUT, 'labels', part, stem + '.txt'), 'w', encoding='utf-8') as fp:
                fp.write('\n'.join(f'{c} {x:.6f} {y:.6f} {w:.6f} {h:.6f}' for c, x, y, w, h in boxes))
    for part, items in neg_all.items():
        for fname in items:
            stem = os.path.splitext(fname)[0]
            link_or_copy(os.path.join(SRC_IMG, fname), os.path.join(OUT, 'images', part, fname))
            open(os.path.join(OUT, 'labels', part, stem + '.txt'), 'w').close()  # 空标签=背景图
            empty_count += 1

    # 5. data.yaml
    yaml = f"""# 跌倒检测数据集 (Fall Dataset) - 由 02_build_dataset.py 生成
path: {OUT.replace(chr(92), '/')}     # 数据集根目录
train: images/train
val: images/val
test: images/test
nc: 1                 # 单类别
names: ['fall']       # 跌倒
"""
    with open(os.path.join(OUT, 'data.yaml'), 'w', encoding='utf-8') as fp:
        fp.write(yaml)

    # 6. 汇总
    print('\n===== 数据集构建完成 =====')
    for part in ('train', 'val', 'test'):
        ni = len(os.listdir(os.path.join(OUT, 'images', part)))
        nl = len(os.listdir(os.path.join(OUT, 'labels', part)))
        print(f'{part}: 图片 {ni}  标签 {nl}')
    print(f'其中负样本(空标签背景图): train {len(neg_all["train"])}  val {len(neg_all["val"])}')
    print('data.yaml ->', os.path.join(OUT, 'data.yaml'))
    # 抽查一个训练标签
    import glob as _g
    sample_lbl = _g.glob(os.path.join(OUT, 'labels', 'train', '*.txt'))[0]
    print('抽查标签:', os.path.basename(sample_lbl))
    print(open(sample_lbl).read().strip())


if __name__ == '__main__':
    sys.exit(main())