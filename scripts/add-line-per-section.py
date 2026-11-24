import io, re

P = r"C:\Users\21674\.openclaw\extensions\wallet-monitor\lines-custom.txt"

EXTRA = {
    "none.idle":      "要不要我把今天的账也记上？",
    "none.idle1":     "骨头咔哒一声，舒服",
    "none.idle2":     "再这样下去要趴在键盘上睡了",
    "none.idle3":     "头发有点乱，等会儿扎起来",
    "none.idle4":     "时间过得好快啊",
    "none.pat":       "再摸我就要赖着不走了",
    "none.angry":     "再点我就把你的代码格式化！",
    "none.legs":      "别戳，腿真的会麻",
    "none.dizzy":     "眼前全是星星…",

    "christmas.idle":  "雪地里踩一脚，咯吱咯吱的",
    "christmas.idle1": "活动一下，不然要冻住了",
    "christmas.idle2": "壁炉的火苗看着就想睡",
    "christmas.idle3": "毛线帽有点痒",
    "christmas.idle4": "天黑了，该挂灯了",
    "christmas.pat":   "你的手比暖手宝还暖",
    "christmas.angry": "再点我就把礼物收回！",
    "christmas.legs":  "雪灌进袜子里了啦",
    "christmas.dizzy": "铃铛声一直在耳朵里转",

    "whale.idle":  "海水味的风，闻着就安心",
    "whale.idle1": "伸展开来，鳍才舒服",
    "whale.idle2": "泡在水里，困意就上来了",
    "whale.idle3": "帽子里好像有小鱼…不对，是错觉",
    "whale.idle4": "算算潮汐，快涨潮了",
    "whale.pat":   "再摸下去我要打呼噜了",
    "whale.angry": "再戳我就用尾巴甩你",
    "whale.legs":  "脚趾包在袜子里，别碰",
    "whale.dizzy": "像被洋流卷走了…",

    "yukata.idle":  "夜市那边好像有苹果糖",
    "yukata.idle1": "袖子太宽，伸懒腰会打到人",
    "yukata.idle2": "逛了一整天，腿好酸",
    "yukata.idle3": "发簪有点松，扶一下",
    "yukata.idle4": "再等一会儿就放烟花了",
    "yukata.pat":   "别弄乱发型，等会儿要拍照",
    "yukata.angry": "再点我就先回去了！",
    "yukata.legs":  "木屐会掉的啦",
    "yukata.dizzy": "烟花在眼前炸开了…",
}

raw = io.open(P, encoding="utf-8").read().replace("\r\n", "\n")
lines = raw.split("\n")

# 切块：header(注释区) + section 列表
blocks = []   # [(key or None, [lines])]
cur_key = None
cur_lines = []
for ln in lines:
    m = re.match(r"^\[([^\]]+)\]$", ln.strip())
    if m:
        blocks.append((cur_key, cur_lines))
        cur_key = m.group(1)
        cur_lines = [ln]
    else:
        cur_lines.append(ln)
blocks.append((cur_key, cur_lines))

added, dup = 0, 0
out_blocks = []
for key, blines in blocks:
    if key and key in EXTRA:
        body = [l for l in blines[1:] if l.strip()]
        if EXTRA[key] in [l.strip() for l in body]:
            dup += 1
        else:
            # 去掉尾部空行后追加
            while blines and blines[-1].strip() == "":
                blines.pop()
            blines.append(EXTRA[key])
            added += 1
    out_blocks.append(blines)

out = []
for blines in out_blocks:
    out.extend(blines)
    if blines and blines[-1].strip() != "":
        out.append("")

text = "\n".join(out).rstrip("\n") + "\n"
io.open(P, "w", encoding="utf-8", newline="\n").write(text)
print("added=%d dup=%d total_sections=%d" % (added, dup, sum(1 for k, _ in blocks if k)))
