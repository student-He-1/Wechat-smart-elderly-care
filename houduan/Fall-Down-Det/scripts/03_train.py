# -*- coding: utf-8 -*-
"""
03_train.py  —— 跌倒检测模型训练脚本
加载本机预训练权重(COCO)微调，加速收敛：
    yolo26n.pt / yolov8n.pt  (位于 d:\\桌面\\Fall-Down-Det\\)

用法示例:
    python scripts/03_train.py --model yolo26n            # 只训 YOLO26n(100轮+早停)
    python scripts/03_train.py --model yolov8n            # 只训 YOLOv8n
    python scripts/03_train.py --model both               # 依次训练两个并做对比
    python scripts/03_train.py --model yolo26n --epochs 200 --batch 16
"""
import argparse, os, sys

if os.name == 'nt':
    # 修复 Anaconda 下 torch 与 numpy/mkl 重复加载 libiomp5md.dll 导致的 OMP Error #15
    os.environ.setdefault('KMP_DUPLICATE_LIB_OK', 'TRUE')

ROOT = r'd:\桌面\Fall-Down-Det'
DATA = os.path.join(ROOT, 'FallDataset-yolo', 'data.yaml')
WEIGHTS = {'yolo26n': os.path.join(ROOT, 'yolo26n.pt'),
           'yolov8n': os.path.join(ROOT, 'yolov8n.pt')}


def train_one(model_key, epochs, imgsz, batch, workers, resume=False):
    from ultralytics import YOLO
    wt = WEIGHTS[model_key]
    if not os.path.exists(wt):
        raise FileNotFoundError(f'预训练权重不存在: {wt}')
    print(f'\n===== 训练 {model_key} | 预训练权重: {wt} =====')
    model = YOLO(wt)                     # 关键：加载已有模型权重，延续 COCO 特征加速收敛
    results = model.train(
        data=DATA,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        workers=workers,
        patience=20,                     # 20 轮无提升自动早停
        optimizer='auto',
        project=os.path.join(ROOT, 'runs', 'train'),
        name=f'{model_key}_fall',
        exist_ok=True,
        resume=resume,
        amp=True,
        val=True,
        seed=42,
    )
    best = model.trainer.best if hasattr(model, 'trainer') else None
    print(f'\n[{model_key}] 训练完成，最佳权重: {best}')
    # 在验证集上复评（val 阶段不支持 AutoBatch 的 -1，固定为正整数）
    val = model.val(split='val', batch=16, imgsz=imgsz)
    print(f'[{model_key}] val 结果 -> mAP50: {val.box.map50:.4f} | '
          f'mAP50-95: {val.box.map:.4f} | P: {val.box.mp:.4f} | R: {val.box.mr:.4f}')
    return model_key, dict(mAP50=val.box.map50, mAP50_95=val.box.map,
                           P=val.box.mp, R=val.box.mr, best=best)


def main():
    ap = argparse.ArgumentParser(description='跌倒检测训练')
    ap.add_argument('--model', default='yolo26n', choices=['yolo26n', 'yolov8n', 'both'],
                    help='训练哪个模型')
    ap.add_argument('--epochs', type=int, default=100)
    ap.add_argument('--imgsz', type=int, default=640, help='训练分辨率')
    ap.add_argument('--batch', type=int, default=-1, help='批量(-1=自动搜索)，6G显存建议16')
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--resume', action='store_true', help='断点续训')
    args = ap.parse_args()

    keys = ['yolo26n', 'yolov8n'] if args.model == 'both' else [args.model]
    summary = {}
    for k in keys:
        if not os.path.exists(os.path.join(ROOT, 'runs', 'train', f'{k}_fall', 'weights', 'best.pt')):
            summary.update(train_one(k, args.epochs, args.imgsz, args.batch, args.workers, args.resume))
        else:
            print(f'检测到已完成的训练结果 {k}_fall，跳过(如需重训请删除对应输出目录)')
            summary[k] = None

    if args.model == 'both':
        print('\n===== 对比汇总 =====')
        for k, m in summary.items():
            if m:
                print(f'{k:10s} mAP50={m["mAP50"]:.4f} mAP50-95={m["mAP50_95"]:.4f} '
                      f'P={m["P"]:.4f} R={m["R"]:.4f} 权重={m["best"]}')


if __name__ == '__main__':
    sys.exit(main())