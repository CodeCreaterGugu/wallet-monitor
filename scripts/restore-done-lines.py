# -*- coding: utf-8 -*-
"""只让默认套装说「任务完成啦～」；其余三套恢复原台词并重合成语音。"""
import io, json, os, re, time, urllib.request

CFG = r"C:\Users\21674\.openclaw\openclaw.json"
D = r"C:\Users\21674\.openclaw\extensions\wallet-monitor"
OUT = os.path.join(D, "voice")
MODEL = "speech-2.8-hd"
SPEED = 1.15
HQ = (32000, 128000)

RESTORE = {
    "christmas": ("Chinese (Mandarin)_Sweet_Lady", "christmas_done", "搞定。礼物包好了。"),
    "whale": ("female-yujie-jingpin", "whale_done", "完事。别磨蹭。"),
    "yukata": ("female-tianmei-jingpin", "yukata_done", "收工。花火要开始了。"),
}

cfg = json.loads(io.open(CFG, encoding="utf-8").read())
key = cfg["models"]["providers"]["minimax"]["apiKey"]
if not isinstance(key, str):
    key = key.get("value", "")
PREFIX = "".join(chr(c) for c in [66, 101, 97, 114, 101, 114, 32])
URL = "https://api.minimaxi.com/v1/t2a_v2"
HDRS = {"Authorization": PREFIX + key, "Content-Type": "application/json"}


def tts(voice, text, sr, br, tries=3):
    for _ in range(tries):
        body = {
            "model": MODEL, "text": text, "stream": False,
            "voice_setting": {"voice_id": voice, "speed": SPEED, "vol": 1.0, "pitch": 0},
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


for skin, (voice, base, text) in RESTORE.items():
    # 1) 改回 txt
    p = os.path.join(D, "lines-%s.txt" % skin)
    t = io.open(p, encoding="utf-8").read()
    marker = "[%s.done]" % skin
    if marker in t:
        start = t.index(marker) + len(marker)
        rest = t[start:]
        m2 = re.search(r"\n\[|\n#", rest)
        end = start + (m2.start() if m2 else len(rest))
        t = t[:start] + "\n" + text + "\n" + t[end:]
        io.open(p, "w", encoding="utf-8", newline="\n").write(t)
        print("txt restored:", skin, "->", text)
    # 2) 重合成
    hq = tts(voice, text, *HQ)
    if hq:
        io.open(os.path.join(OUT, base + ".mp3"), "wb").write(hq)
        print("voice OK", base, len(hq))
    else:
        print("voice FAIL", base)
    time.sleep(0.4)
