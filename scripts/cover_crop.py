#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
从等距柱状全景图裁一张 16:9 透视封面（供 catalog/assets/covers/ 使用）。

用法：
  python scripts/cover_crop.py <全景图.jpg> <输出.jpg> [--yaw 10] [--pitch 0] [--fov 75]

坐标约定与 tour_spec / 播放器一致：yaw 0° = 扫拍起始方向（全景图水平原点），
沿经度增大方向旋转；pitch 正值朝上；fov 为水平视角（度）。
经验：优先朝室内主体方向（yaw 避开窗户/阳台方向，否则逆光发黑），
pitch 0 附近最稳。全景图上半为天空（v=0 对应天顶）。
无 opencv 时自动退回纯 PIL 实现（双线性，稍慢，效果足够 1600px 封面用）。
"""
import argparse, sys

# Windows 控制台默认 GBK，中文与 ✓ 会炸；统一转 UTF-8（与 build_tour.py 同法）
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def crop_cv2(src, out, yaw, pitch, fov, ow, oh):
    import numpy as np, cv2
    import os
    img = cv2.imdecode(np.fromfile(src, dtype=np.uint8), cv2.IMREAD_COLOR)  # cv2 打不开中文路径
    if img is None:
        sys.exit(f"× 无法读取全景图：{src}")
    H, W = img.shape[:2]
    f = ow / 2 / np.tan(np.radians(fov) / 2)
    x, y = np.meshgrid(np.arange(ow) - ow / 2 + 0.5, oh / 2 - np.arange(oh) - 0.5)
    r = np.sqrt(x * x + y * y + f * f)
    lon = np.arctan2(x, f) + np.radians(yaw)
    lat = np.arcsin(y / r) + np.radians(pitch)
    u = (lon / (2 * np.pi) % 1.0) * W
    v = (0.5 - lat / np.pi) * H
    res = cv2.remap(img, u.astype(np.float32), np.clip(v, 0, H - 1).astype(np.float32),
                    cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_WRAP)
    ok, buf = cv2.imencode(".jpg", res, [cv2.IMWRITE_JPEG_QUALITY, 88])
    if not ok:
        sys.exit("× JPEG 编码失败")
    buf.tofile(out)
    return "opencv"


def crop_pil(src, out, yaw, pitch, fov, ow, oh):
    from PIL import Image
    import math
    img = Image.open(src).convert("RGB")
    W, H = img.size
    f = ow / 2 / math.tan(math.radians(fov) / 2)
    yaw_r, pitch_r = math.radians(yaw), math.radians(pitch)
    out_px = bytearray(ow * oh * 3)
    px = img.load()
    for j in range(oh):
        y = oh / 2 - j - 0.5
        for i in range(ow):
            x = i - ow / 2 + 0.5
            r = math.sqrt(x * x + y * y + f * f)
            lon = math.atan2(x, f) + yaw_r
            lat = math.asin(y / r) + pitch_r
            u = (lon / (2 * math.pi)) % 1.0
            v = 0.5 - lat / math.pi
            su = min(W - 1, max(0, int(u * W)))
            sv = min(H - 1, max(0, int(v * H)))
            p = px[su, sv]
            o = (j * ow + i) * 3
            out_px[o:o + 3] = bytes(p)
    Image.frombytes("RGB", (ow, oh), bytes(out_px)).save(out, quality=88)
    return "pillow"


def main():
    ap = argparse.ArgumentParser(description="等距柱状全景 → 16:9 透视封面")
    ap.add_argument("src"); ap.add_argument("out")
    ap.add_argument("--yaw", type=float, default=0.0, help="水平角，0=扫拍起始方向")
    ap.add_argument("--pitch", type=float, default=0.0, help="俯仰角，正值为朝上")
    ap.add_argument("--fov", type=float, default=75.0, help="水平视角（度）")
    ap.add_argument("--width", type=int, default=1600)
    args = ap.parse_args()
    ow, oh = args.width, args.width * 9 // 16
    try:
        engine = crop_cv2(args.src, args.out, args.yaw, args.pitch, args.fov, ow, oh)
    except ImportError:
        engine = crop_pil(args.src, args.out, args.yaw, args.pitch, args.fov, ow, oh)
    import os
    print(f"✓ 封面已生成（{engine}）：{args.out}  {ow}x{oh}  {os.path.getsize(args.out)//1024} KB  yaw={args.yaw} pitch={args.pitch} fov={args.fov}")


if __name__ == "__main__":
    main()
