import io, os, glob
from PIL import Image

SPR = r"C:\Users\21674\.openclaw\extensions\wallet-monitor\sprites"
REF = r"C:\Users\21674\.openclaw\media\crab-refs"
GEN = r"C:\Users\21674\.openclaw\media\tool-image-generation"

def latest(pat):
    hits = sorted(glob.glob(os.path.join(GEN, pat)), key=os.path.getmtime)
    return hits[-1] if hits else None

srcs = {
    "skinprev_none": os.path.join(SPR, "idle.webp"),
    "skinprev_christmas": os.path.join(REF, "xmas-base.png"),
    "skinprev_whale": os.path.join(REF, "approved-whale-slippers.png"),
    "skinprev_yukata": latest("design-05f-yukata-woodhandle---*.png"),
}

TARGET_H = 260

def to_thumb(src, dst):
    im = Image.open(src).convert("RGBA")
    px = im.load()
    w, h = im.size
    # 去白底：接近纯白 -> 透明
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if r >= 244 and g >= 244 and b >= 244:
                px[x, y] = (r, g, b, 0)
    bbox = im.getbbox()
    if bbox:
        im = im.crop(bbox)
    scale = TARGET_H / float(im.height)
    im = im.resize((max(1, int(im.width * scale)), TARGET_H), Image.LANCZOS)
    im.save(dst, "WEBP", quality=88, method=4)
    return im.size

for key, src in srcs.items():
    if not src or not os.path.exists(src):
        print("MISS", key, src)
        continue
    out = os.path.join(SPR, key + ".webp")
    print(key, "->", to_thumb(src, out))
