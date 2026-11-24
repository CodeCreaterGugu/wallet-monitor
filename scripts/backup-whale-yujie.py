# -*- coding: utf-8 -*-
"""把鲸鱼的 MiniMax 御姐版重新生成一份，存到备份目录（不影响当前 voice/）。"""
import io, json, os, re, time, urllib.request

CFG = r"C:\Users\21674\.openclaw\openclaw.json"
D = r"C:\Users\21674\.openclaw\extensions\wallet-monitor"
OUT = r"D:\AI生成\语音\鲸鱼_御姐MiniMax备份"
os.makedirs(OUT, exist_ok=True)

VOICE = "female-yujie-jingpin"
MODEL = "speech-2.8-hd"
SPEED = 1.15
HQ = (32000, 128000)
LQ = (24000, 32000)
LQ_THRESHOLD = 45000

cfg = json.loads(io.open(CFG, encoding="utf-8").read())
key = cfg["models"]["providers"]["minimax"]["apiKey"]
if not isinstance(key, str):
    key = key.get("value", "")
PREFIX = "".join(chr(c) for c in [66, 101, 97, 114, 101, 114, 32])
URL = "https://api.minimaxi.com/v1/t2a_v2"
HDRS = {"Authorization": PREFIX + key, "Content-Type": "application/json"}


def fnv(text):
    h = 0x811C9DC5
    for b in text.encode("utf-8"):
        h ^= b
        h = (h * 0x01000193) & 0xFFFFFFFF
    return format(h, "08x")


def tts(text, sr, br, tries=3):
    for _ in range(tries):
        body = {
            "model": MODEL, "text": text, "stream": False,
            "voice_setting": {"voice_id": VOICE, "speed": SPEED, "vol": 1.0, "pitch": 0},
            "audio_setting": {"sample_rate": sr, "bitrate": br, "format": "mp3"},
        }
        try:
            req = urllib.request.Request(URL, data=json.dumps(body).encode("utf-8"), method="POST", headers=HDRS)
            r = json.loads(urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace"))
            a = (r.get("data") or {}).get("audio")
            if a:
                return bytes.fromhex(a)
        except Exception:
            pass
        time.sleep(1.5)
    return b""


TXT = os.path.join(D, "lines-whale.txt")
sec, data = None, {}
for ln in io.open(TXT, encoding="utf-8"):
    s = ln.strip()
    m = re.match(r"^\[([^\]]+)\]$", s)
    if m:
        sec = m.group(1)
        continue
    if sec and s and not s.startswith("#"):
        data.setdefault(sec, []).append(s)

ok = 0
for kind in ["pat", "angry", "legs", "dizzy"]:
    for i, text in enumerate(data.get("whale." + kind, []), 1):
        for base in ("line_whale_%s_%d" % (kind, i), "cus_whale_%s" % fnv(text)):
            hq = tts(text, *HQ)
            if hq:
                io.open(os.path.join(OUT, base + ".mp3"), "wb").write(hq)
                if len(hq) > LQ_THRESHOLD:
                    low = tts(text, *LQ)
                    if low:
                        io.open(os.path.join(OUT, base + "_lq.mp3"), "wb").write(low)
                ok += 1
            time.sleep(0.25)

SYS = {"whale.done": "whale_done", "whale.full": "whale_full", "whale.sad": "whale_sad",
       "whale.panel_low": "line_whale_panel_low", "whale.panel_high": "line_whale_panel_high"}
for k, base in SYS.items():
    lines = data.get(k, [])
    if not lines:
        continue
    hq = tts(lines[0], *HQ)
    if hq:
        io.open(os.path.join(OUT, base + ".mp3"), "wb").write(hq)
        ok += 1
    time.sleep(0.25)

print("backup files:", ok, "->", OUT)
