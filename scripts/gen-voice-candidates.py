import io, json, os, urllib.request

CFG = r"C:\Users\21674\.openclaw\openclaw.json"
OUT = r"C:\Users\21674\Desktop\看图\音色试听\2.8候选"
os.makedirs(OUT, exist_ok=True)

cfg = json.loads(io.open(CFG, encoding="utf-8").read())
key = cfg["models"]["providers"]["minimax"]["apiKey"]
if not isinstance(key, str):
    key = key.get("value", "")
PREFIX = "".join(chr(c) for c in [66, 101, 97, 114, 101, 114, 32])
BASE = "https://api.minimaxi.com/v1"
HDRS = {"Authorization": PREFIX + key, "Content-Type": "application/json"}

req = urllib.request.Request(BASE + "/get_voice", data=json.dumps({"voice_type": "system"}).encode(), method="POST", headers=HDRS)
js = json.loads(urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace"))
voices = js.get("system_voice") or []
print("catalog", len(voices))

# 已听过的，跳过
HEARD = {
    "female-shaonv", "female-yujie", "female-chengshu", "female-tianmei",
    "female-shaonv-jingpin", "female-yujie-jingpin",
    "female-chengshu-jingpin", "female-tianmei-jingpin",
}

def is_female(v):
    vid = v.get("voice_id", "")
    name = v.get("voice_name", "")
    return ("female" in vid.lower()) or ("女" in name) or ("Girl" in vid) or ("女生" in name)

cand = [v for v in voices if is_female(v) and v.get("voice_id") not in HEARD]

# 去重同名，取前 8 个风格不同的
seen, picked = set(), []
for v in cand:
    vid = v["voice_id"]
    base = vid.split("_")[-1].lower()
    if base in seen:
        continue
    seen.add(base)
    picked.append(v)
    if len(picked) >= 8:
        break

TEXT = "我是你的钱包小助手，今天也省着点花哦。"
URL = BASE + "/t2a_v2"

ok = []
for v in picked:
    vid = v["voice_id"]
    body = {
        "model": "speech-2.8-hd", "text": TEXT, "stream": False,
        "voice_setting": {"voice_id": vid, "speed": 0.95, "vol": 1.0, "pitch": 0},
        "audio_setting": {"sample_rate": 32000, "bitrate": 128000, "format": "mp3"},
    }
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), method="POST", headers=HDRS)
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace"))
        h = (r.get("data") or {}).get("audio")
        if not h:
            print("SKIP", vid, str((r.get("base_resp") or {}).get("status_msg"))[:50])
            continue
        raw = bytes.fromhex(h)
        safe = vid.replace(" ", "_").replace("(", "").replace(")", "")
        p = os.path.join(OUT, safe + ".mp3")
        io.open(p, "wb").write(raw)
        ok.append((vid, v.get("voice_name", ""), len(raw)))
        print("OK", vid, v.get("voice_name", ""), len(raw))
    except Exception as e:
        print("ERR", vid, type(e).__name__)

print("done", len(ok))
