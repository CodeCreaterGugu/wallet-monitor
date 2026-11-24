# -*- coding: utf-8 -*-
"""默认套装语音：按原始参数 32kHz/128kbps 重做；超大文件额外压一份 _lq 备用。"""
import io, json, os, re, time, urllib.request

CFG = r"C:\Users\21674\.openclaw\openclaw.json"
D = r"C:\Users\21674\.openclaw\extensions\wallet-monitor"
OUT = os.path.join(D, "voice")
TXT = os.path.join(D, "lines-none.txt")
VOICE = "female-shaonv"
MODEL = "speech-2.8-hd"
SPEED = 1.15
HQ = (32000, 128000)
LQ = (24000, 32000)
LQ_THRESHOLD = 45000   # 超过这个字节数就再存一份低码率备用

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


sec, data = None, {}
for ln in io.open(TXT, encoding="utf-8"):
    s = ln.strip()
    m = re.match(r"^\[([^\]]+)\]$", s)
    if m:
        sec = m.group(1)
        continue
    if sec and s and not s.startswith("#"):
        data.setdefault(sec, []).append(s)


def tts(text, sr, br, tries=3):
    for i in range(tries):
        body = {
            "model": MODEL,
            "text": text,
            "stream": False,
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


def save(text, base_name):
    hq = tts(text, *HQ)
    if not hq:
        return 0, 0
    io.open(os.path.join(OUT, base_name + ".mp3"), "wb").write(hq)
    lq = 0
    if len(hq) > LQ_THRESHOLD:
        low = tts(text, *LQ)
        if low:
            io.open(os.path.join(OUT, base_name + "_lq.mp3"), "wb").write(low)
            lq = len(low)
    return len(hq), lq


total = 0
for kind in ["pat", "angry", "legs", "dizzy"]:
    for i, text in enumerate(data.get("none." + kind, []), 1):
        seq_name = "line_%s_%d" % (kind, i)
        a, b = save(text, seq_name)
        c, d = save(text, "cus_" + fnv(text))
        total += 2
        print("%-6s %d hq=%dB lq=%dB  %s" % (kind, i, a, b, text))
        time.sleep(0.3)

SYS = {
    "none.done": "done",
    "none.full": "full",
    "none.sad": "sad",
    "none.panel_low": "line_panel_low",
    "none.panel_high": "line_panel_high",
}
for k, base in SYS.items():
    lines = data.get(k, [])
    if not lines:
        continue
    a, b = save(lines[0], base)
    total += 1
    print("%-14s hq=%dB lq=%dB  %s" % (k, a, b, lines[0]))
    time.sleep(0.3)

print("done", total)
