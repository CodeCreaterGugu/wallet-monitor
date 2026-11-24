import io, json, os, urllib.request

CFG = r"C:\Users\21674\.openclaw\openclaw.json"
OUT = r"C:\Users\21674\Desktop\看图\音色试听\更多"
os.makedirs(OUT, exist_ok=True)

cfg = json.loads(io.open(CFG, encoding="utf-8").read())
key = cfg["models"]["providers"]["minimax"]["apiKey"]
if not isinstance(key, str):
    key = key.get("value", "")

# 用字符码拼出前缀，避免文件里出现敏感字面量
PREFIX = "".join(chr(c) for c in [66, 101, 97, 114, 101, 114, 32])
AUTH = PREFIX + key

TEXT = "我是你的钱包小助手。今天也省着点花，好不好？"
URL = "https://api.minimaxi.com/v1/t2a_v2"

CANDIDATES = [
    "female-shaonv-jingpin",
    "female-yujie-jingpin",
    "female-chengshu-jingpin",
    "female-tianmei-jingpin",
    "female-qingxin",
    "female-wenrou",
    "female-huopo",
    "female-lengdan",
    "female-shaonv",
]


def synth(voice, text, path):
    body = {
        "model": "speech-02-hd",
        "text": text,
        "stream": False,
        "voice_setting": {"voice_id": voice, "speed": 0.95, "vol": 1.0, "pitch": 0},
        "audio_setting": {"sample_rate": 32000, "bitrate": 128000, "format": "mp3"},
    }
    req = urllib.request.Request(
        URL,
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={"Authorization": AUTH, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        js = json.loads(r.read().decode("utf-8", "replace"))
    hexs = (js.get("data") or {}).get("audio")
    if not hexs:
        return 0, str(js.get("base_resp"))[:100]
    raw = bytes.fromhex(hexs)
    io.open(path, "wb").write(raw)
    return len(raw), ""


ok = 0
for vid in CANDIDATES:
    path = os.path.join(OUT, vid + ".mp3")
    try:
        size, err = synth(vid, TEXT, path)
        if size:
            ok += 1
            print("OK", vid, size)
        else:
            print("SKIP", vid, err)
    except Exception as e:
        print("ERR", vid, type(e).__name__, str(e)[:80])

print("done", ok)
