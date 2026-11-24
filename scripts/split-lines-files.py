# -*- coding: utf-8 -*-
import io, os, re

D = r"C:\Users\21674\.openclaw\extensions\wallet-monitor"
SRC = os.path.join(D, "lines-custom.txt")

raw = io.open(SRC, encoding="utf-8").read()
sec = None
data = {}
order = []
for ln in raw.split("\n"):
    s = ln.strip()
    m = re.match(r"^\[([^\]]+)\]$", s)
    if m:
        sec = m.group(1)
        data[sec] = []
        order.append(sec)
        continue
    if sec and s and not s.startswith("#") and not s.startswith("//"):
        data[sec].append(s)

KINDS = ["idle", "idle1", "idle2", "idle3", "idle4", "pat", "angry", "legs", "dizzy"]

SYSTEM = {
    "none": {
        "done": ["任务完成。辛苦你了。"],
        "full": ["收到了。我吃饱了。"],
        "sad": ["余额不多了。省着点用。"],
        "panel_low": ["快见底了。要充吗？"],
        "panel_high": ["还够用。别乱花。"],
    },
    "christmas": {
        "done": ["搞定。礼物包好了。"],
        "full": ["到账了。这份我收下。"],
        "sad": ["钱包比外面还冷。"],
        "panel_low": ["快没钱买礼物了。"],
        "panel_high": ["够买礼物的。"],
    },
    "whale": {
        "done": ["完事。别磨蹭。"],
        "full": ["到账。我记下了。"],
        "sad": ["余额见底。别指望我垫。"],
        "panel_low": ["快没了。自己看着办。"],
        "panel_high": ["还够。省着点。"],
    },
    "yukata": {
        "done": ["收工。花火要开始了。"],
        "full": ["收到。够逛祭典了。"],
        "sad": ["钱不够逛祭典了。"],
        "panel_low": ["只剩一点了。"],
        "panel_high": ["还够买苹果糖。"],
    },
}

TITLES = {
    "none": "默认套装",
    "christmas": "圣诞装",
    "whale": "鲸鱼装",
    "yukata": "和服装",
}

HEAD = """# ============================================================
# %s · 专属台词
# 文件：extensions\\wallet-monitor\\lines-%s.txt
# ============================================================
# 这个文件只放这一套服装说的话；段落一律写成 [%s.动作]。
# 改完保存 → 刷新 Control UI 页面生效，不用重启。
#
# 动作：idle / idle1(伸懒腰) / idle2(打哈欠) / idle3(挠头) / idle4(看表)
#       pat(摸头) / angry(点身子) / legs(点腿) / dizzy(双击)
# 系统：done(任务完成) / full(充值到账) / sad(余额告急)
#       panel_low(点气泡·余额告急) / panel_high(点气泡·余额充足)
#
# 语音：只有 pat / angry / legs / dizzy / done / full / sad / panel_* 出声；
#       所有 idle 系列纯文字。
# ============================================================
"""

for skin in ["none", "christmas", "whale", "yukata"]:
    out = [HEAD % (TITLES[skin], skin, skin), ""]
    out.append("# -------------------- 台词 --------------------")
    for k in KINDS:
        key = "%s.%s" % (skin, k)
        lines = data.get(key) or []
        out.append("[%s]" % key)
        out.extend(lines if lines else ["（待填）"])
        out.append("")
    out.append("# -------------------- 系统语音 --------------------")
    for k, lines in SYSTEM[skin].items():
        out.append("[%s.%s]" % (skin, k))
        out.extend(lines)
        out.append("")
    p = os.path.join(D, "lines-%s.txt" % skin)
    io.open(p, "w", encoding="utf-8", newline="\n").write("\n".join(out).rstrip("\n") + "\n")
    print("wrote", p, "sections", len(KINDS) + len(SYSTEM[skin]))

# 主文件只留说明 + 系统语音清单（不再放台词，避免和专属文件重复）
MAIN = """# ============================================================
# 台词库 · 总说明
# ============================================================
# 台词现在按服装拆成四个文件，本文件只放公共说明：
#
#   lines-none.txt        默认套装
#   lines-christmas.txt   圣诞装
#   lines-whale.txt       鲸鱼装
#   lines-yukata.txt      和服装
#
# 每个文件里写 [皮肤.动作] 段落，例如 [whale.pat]。
# 改完保存 → 刷新 Control UI 页面生效，不用重启。
#
# 系统语音清单（这些也走同一套文本机制，写在各自文件末尾）：
#   done / full / sad / panel_low / panel_high
# 音效类（不配音）：giggle 笑声、dizzy_fx 眩晕音效
# ============================================================
"""
io.open(SRC, "w", encoding="utf-8", newline="\n").write(MAIN)
print("rewrote lines-custom.txt as index only")
