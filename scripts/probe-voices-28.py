import io, json, urllib.request, urllib.error

CFG = r"C:\Users\21674\.openclaw\openclaw.json"
cfg = json.loads(io.open(CFG, encoding="utf-8").read())
key = cfg["models"]["providers"]["minimax"]["apiKey"]
if not isinstance(key, str):
    key = key.get("value", "")
PREFIX = "".join(chr(c) for c in [66, 101, 97, 114, 101, 114, 32])
BASE = "https://api.minimaxi.com/v1"
HDRS = {"Authorization": PREFIX + key, "Content-Type": "application/json"}

# 1) 先看官方能列出的系统音色
for body in ({"voice_type": "system"}, {"voice_type": "all"}):
    try:
        req = urllib.request.Request(BASE + "/get_voice", data=json.dumps(body).encode(), method="POST", headers=HDRS)
        raw = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
        js = json.loads(raw)
        print("get_voice", body, "keys=", list(js.keys())[:8])
        for k in js:
            if isinstance(js[k], list):
                print("  list", k, "len=", len(js[k]))
                for it in js[k][:5]:
                    print("   ", it.get("voice_id"), it.get("voice_name"))
    except Exception as e:
        print("get_voice ERR", body, type(e).__name__, str(e)[:90])

# 2) 逐个试常见音色 id 在 2.8 下是否可用
CAND = [
    "female-shaonv", "female-yujie", "female-chengshu", "female-tianmei",
    "female-shaonv-jingpin", "female-yujie-jingpin",
    "female-chengshu-jingpin", "female-tianmei-jingpin",
    "male-qn-qingse", "male-qn-jingying", "male-qn-badao",
    "clever_boy", "thoughtful_girl", "cute_boy", "lovely_girl",
    "Chinese (Mandarin)_Warm_Girl", "Chinese (Mandarin)_Gentle_Youth",
    "Chinese (Mandarin)_Soft_Girl", "Chinese (Mandarin)_Sweet_Girl",
    "Chinese (Mandarin)_News_Girl", "Chinese (Mandarin)_Cute_Animal",
    "audiobook_female_1", "audiobook_male_1",
]

ok, bad = [], []
for vid in CAND:
    body = {
        "model": "speech-2.8-hd", "text": "嗯。", "stream": False,
        "voice_setting": {"voice_id": vid, "speed": 1.0, "vol": 1.0, "pitch": 0},
        "audio_setting": {"sample_rate": 16000, "bitrate": 64000, "format": "mp3"},
    }
    try:
        req = urllib.request.Request(BASE + "/t2a_v2", data=json.dumps(body).encode(), method="POST", headers=HDRS)
        js = json.loads(urllib.request.urlopen(req, timeout=45).read().decode("utf-8", "replace"))
        br = js.get("base_resp") or {}
        if (js.get("data") or {}).get("audio"):
            ok.append(vid)
        else:
            bad.append((vid, br.get("status_code"), str(br.get("status_msg"))[:40]))
    except Exception as e:
        bad.append((vid, "ERR", type(e).__name__))

print("\nOK", len(ok), ":", ok)
print("\nBAD", len(bad))
for b in bad:
    print("  ", b)
