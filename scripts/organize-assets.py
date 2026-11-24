# -*- coding: utf-8 -*-
"""把 wallet-monitor（蟹娘钱包）相关素材整理到 D:\\AI生成\\WalletCrab。仅复制，不动插件目录。"""
import os
import shutil

ROOT = r"D:\AI生成\WalletCrab"
PLUG = r"C:\Users\21674\.openclaw\extensions\wallet-monitor"
MEDIA = r"C:\Users\21674\.openclaw\media"

DIRS = [
    "01_立绘_当前",
    "02_素材_生成图",
    "03_语音_当前",
    "03_语音_备份",
    "04_文档",
    "05_参考图",
    "06_打包",
]
for d in DIRS:
    os.makedirs(os.path.join(ROOT, d), exist_ok=True)


def copy_tree(src, dst, pattern=None):
    if not os.path.isdir(src):
        print("MISS", src)
        return 0
    n = 0
    for name in os.listdir(src):
        s = os.path.join(src, name)
        if not os.path.isfile(s):
            continue
        if pattern and not pattern(name):
            continue
        shutil.copy2(s, os.path.join(dst, name))
        n += 1
    return n


# 立绘 / 语音
print("立绘:", copy_tree(os.path.join(PLUG, "sprites"), os.path.join(ROOT, "01_立绘_当前")))
print("语音:", copy_tree(os.path.join(PLUG, "voice"), os.path.join(ROOT, "03_语音_当前")))

# 语音备份
vb = r"D:\AI生成\语音"
if os.path.isdir(vb):
    n = 0
    for name in os.listdir(vb):
        s = os.path.join(vb, name)
        d = os.path.join(ROOT, "03_语音_备份", name)
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True)
            n += 1
        elif os.path.isfile(s):
            shutil.copy2(s, os.path.join(ROOT, "03_语音_备份", name))
            n += 1
    print("语音备份项:", n)

# 文档
docs = [
    "PERSONAS.md", "ROADMAP.md", "POSE-PLAN.md", "POSES-MATRIX.md", "HANDOFF.md",
    "lines-custom.txt", "lines-none.txt", "lines-christmas.txt", "lines-whale.txt", "lines-yukata.txt",
]
n = 0
for d in docs:
    p = os.path.join(PLUG, d)
    if os.path.isfile(p):
        shutil.copy2(p, os.path.join(ROOT, "04_文档", d))
        n += 1
print("插件文档:", n)

extra = [
    r"D:\AI生成\文档\钱包监控插件-改造方案.md",
    r"D:\AI生成\文档\wallet-monitor-待机小动作问题说明.md",
]
n = 0
for p in extra:
    if os.path.isfile(p):
        shutil.copy2(p, os.path.join(ROOT, "04_文档", os.path.basename(p)))
        n += 1
print("外部文档:", n)

# 打包
for p in [r"D:\AI生成\文档\wallet-monitor-src-20261103.zip"]:
    if os.path.isfile(p):
        shutil.copy2(p, os.path.join(ROOT, "06_打包", os.path.basename(p)))
        print("打包: ok")

# 参考图
print("参考图:", copy_tree(os.path.join(MEDIA, "crab-refs"), os.path.join(ROOT, "05_参考图")))
# 参考图子目录
for sub in ("pose-src",):
    s = os.path.join(MEDIA, "crab-refs", sub)
    if os.path.isdir(s):
        shutil.copytree(s, os.path.join(ROOT, "05_参考图", sub), dirs_exist_ok=True)

# 生成图（只收本项目相关命名）
def relevant(name):
    k = name.lower()
    keys = ("christmas", "xmas", "yukata", "whale", "design_devil", "wm_", "crab")
    return k.endswith((".png", ".jpg", ".jpeg", ".webp")) and any(x in k for x in keys)

print("生成图:", copy_tree(os.path.join(MEDIA, "tool-image-generation"), os.path.join(ROOT, "02_素材_生成图"), relevant))

# 看图目录整体复制（保留子目录结构）
view = r"D:\AI生成\看图"
if os.path.isdir(view):
    shutil.copytree(view, os.path.join(ROOT, "02_素材_生成图", "看图归档"), dirs_exist_ok=True)
    print("看图归档: ok")

# 统计
total = 0
cnt = 0
for base, _, files in os.walk(ROOT):
    for f in files:
        total += os.path.getsize(os.path.join(base, f))
        cnt += 1
print("总计 %d 个文件，%.1f MB -> %s" % (cnt, total / 1024 / 1024, ROOT))
