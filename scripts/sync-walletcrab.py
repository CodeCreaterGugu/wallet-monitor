# -*- coding: utf-8 -*-
"""把最新素材同步到 D:\\AI生成\\WalletCrab，并把已导入的抠图归档。"""
import glob
import os
import shutil

PLUG = r"C:\Users\21674\.openclaw\extensions\wallet-monitor"
MEDIA = r"C:\Users\21674\.openclaw\media"
ROOT = r"D:\AI生成\WalletCrab"
CUT = r"C:\Users\21674\Desktop\待抠图"

log = []


def sync_files(src_glob, dst, label):
    os.makedirs(dst, exist_ok=True)
    n = 0
    for p in glob.glob(src_glob):
        if os.path.isfile(p):
            shutil.copy2(p, os.path.join(dst, os.path.basename(p)))
            n += 1
    log.append("%s: %d" % (label, n))
    return n


# 1) 立绘
sync_files(os.path.join(PLUG, "sprites", "*.webp"), os.path.join(ROOT, "01_立绘_当前"), "立绘同步")
# 2) 语音
sync_files(os.path.join(PLUG, "voice", "*.mp3"), os.path.join(ROOT, "03_语音_当前"), "语音同步")
sync_files(os.path.join(PLUG, "voice", "*.wav"), os.path.join(ROOT, "03_语音_当前"), "音效同步")
# 3) 文档
for name in ["PERSONAS.md", "ROADMAP.md", "POSE-PLAN.md", "POSES-MATRIX.md", "HANDOFF.md",
             "lines-custom.txt", "lines-none.txt", "lines-christmas.txt", "lines-whale.txt", "lines-yukata.txt"]:
    p = os.path.join(PLUG, name)
    if os.path.isfile(p):
        shutil.copy2(p, os.path.join(ROOT, "04_文档", name))
log.append("文档同步: 完成")
# 4) 参考图（含三视图、基准）
sync_files(os.path.join(MEDIA, "crab-refs", "*.png"), os.path.join(ROOT, "05_参考图"), "参考图同步")

# 5) 归档已导入的抠图
arc = os.path.join(ROOT, "02_素材", "已抠图", "yukata")
os.makedirs(arc, exist_ok=True)
moved = 0
for p in glob.glob(os.path.join(CUT, "皮肤", "yukata_*.png")):
    shutil.move(p, os.path.join(arc, os.path.basename(p)))
    moved += 1
for p in glob.glob(os.path.join(CUT, "缩略图", "skinprev_none.png")):
    shutil.move(p, os.path.join(ROOT, "02_素材", "已抠图", os.path.basename(p)))
    moved += 1
log.append("归档抠图: %d" % moved)

print("\n".join(log))
print("\n待抠图剩余:")
for sub in ["皮肤", "缩略图"]:
    d = os.path.join(CUT, sub)
    if os.path.isdir(d):
        print(" ", sub, len(os.listdir(d)), "files")
