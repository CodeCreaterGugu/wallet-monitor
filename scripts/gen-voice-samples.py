import io, json, os, urllib.request

CFG = r"C:\Users\21674\.openclaw\openclaw.json"
OUT = r"C:\Users\21674\Desktop\看图\音色试听"
os.makedirs(OUT, exist_ok=True)

cfg = json.loads(io.open(CFG, encoding="utf-8").read())
key = cfg["models"]["providers"]["minimax"]["apiKey"]
if not isinstance(key, str):
    key = key.get("value", "")

SAMPLES = [
    ("none", "female-shaonv",
     "我是你的钱包小助手。平时喜欢窝在屏幕角落看书，顺手帮你盯着余额。今天也省着点花哦。"),
    ("christmas", "female-tianmei",
     "圣诞快乐！我换了新衣服，帽子上还多了两只小蟹钳。外面在下雪，记得喝热可可，别冻着手。"),
    ("whale", "female-yujie",
     "我是从海里来的。帽子戴好了，尾巴不许拉。陆地上有点热，让我在这儿趴一会儿吧。"),
    ("yukata", "female-chengshu",
     "今晚有花火大会，我穿了浴衣。木屐不太好走，你等等我呀，别走那么快。"),
]

URL = "https://api.minimaxi.com/v1/t2a_v2"

for skin, voice, text in SAMPLES:
    body = {
        "model": "speech-02-hd",
        "text": text,
        "stream": False,
        "voice_setting": {"voice_id": voice, "speed": 0.95, "vol": 1.0, "pitch": 0},
        "audio_setting": {"sample_rate": 32000, "bitrate": 128000, "format": "mp3"},
    }
    req = urllib.request.Request(
        URL, data=json.dumps(body).encode("utf-8"), method="POST",
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        js = json.loads(r.read().decode("utf-8", "replace"))
    audio_hex = js.get("data", {}).get("audio")
    if not audio_hex:
        print(skin, "FAIL", str(js.get("base_resp"))[:120])
        continue
    raw = bytes.fromhex(audio_hex)
    path = os.path.join(OUT, "%s_%s.mp3" % (skin, voice))
    io.open(path, "wb").write(raw)
    print(skin, voice, len(raw), "bytes ->", path)
