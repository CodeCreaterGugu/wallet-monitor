# -*- coding: utf-8 -*-
"""1) 默认套还原 MiniMax 少女音  2) 和服套改用甜美桃子（语速 +15），原和服先备份"""
import io, json, os, re, shutil, sys, time, uuid

D = r"C:\Users\21674\.openclaw\extensions\wallet-monitor"
VOICE = os.path.join(D, "voice")
sys.path.insert(0, os.path.join(D, "scripts"))
from ws_tts import (WS, build, next_msg, HOST, PATH, EV_START_CONN, EV_START_SESSION,
                    EV_FINISH_SESSION, EV_TASK_REQUEST, EV_SESSION_FINISHED,
                    EV_TTS_RESPONSE, T_AUDIO_SERVER, T_ERROR)

KEY_PATH = r"C:\Users\21674\Desktop\重要文件\API KEY.txt"
SPEAKER = "zh_female_tianmeitaozi_uranus_bigtts"
RATE = 15
BACKUP_NONE = r"D:\AI生成\语音\默认_MiniMax备份"
BACKUP_YK = r"D:\AI生成\语音\和服_MiniMax备份"

# ---- 1) 还原默认 ----
restored = 0
if os.path.isdir(BACKUP_NONE):
    for f in os.listdir(BACKUP_NONE):
        shutil.copy2(os.path.join(BACKUP_NONE, f), os.path.join(VOICE, f))
        restored += 1
print("restored default files:", restored)

cands = []
for line in io.open(KEY_PATH, encoding="utf-8"):
    t = line.strip()
    if not t:
        continue
    if ":" in t:
        v = t.split(":", 1)[1].strip()
        if len(v) >= 20:
            cands.append(v)
    elif len(t) >= 20:
        cands.append(t)
KEY = cands[-1]


def fnv(text):
    h = 0x811C9DC5
    for b in text.encode("utf-8"):
        h ^= b
        h = (h * 0x01000193) & 0xFFFFFFFF
    return format(h, "08x")


TXT = os.path.join(D, "lines-yukata.txt")
sec, data = None, {}
for ln in io.open(TXT, encoding="utf-8"):
    s = ln.strip()
    m = re.match(r"^\[([^\]]+)\]$", s)
    if m:
        sec = m.group(1)
        continue
    if sec and s and not s.startswith("#"):
        data.setdefault(sec, []).append(s)

names = []
for kind in ["pat", "angry", "legs", "dizzy"]:
    for i, text in enumerate(data.get("yukata." + kind, []), 1):
        names.append("line_yukata_%s_%d" % (kind, i))
        names.append("cus_yukata_%s" % fnv(text))
names += ["yukata_done", "yukata_full", "yukata_sad", "line_yukata_panel_low", "line_yukata_panel_high"]

# ---- 备份和服 ----
os.makedirs(BACKUP_YK, exist_ok=True)
bk = 0
for n in names:
    for suffix in (".mp3", "_lq.mp3"):
        src = os.path.join(VOICE, n + suffix)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(BACKUP_YK, n + suffix))
            bk += 1
print("backup yukata:", bk, "->", BACKUP_YK)


def synth(text, path):
    ws = WS(HOST, PATH, {
        "X-Api-Key": KEY,
        "X-Api-Resource-Id": "seed-tts-2.0",
        "X-Api-Connect-Id": str(uuid.uuid4()),
    })
    ws.send(build(EV_START_CONN, payload=b"{}"))
    m = next_msg(ws)
    if not m or m["event"] != 50:
        raise RuntimeError("conn failed")
    sid = str(uuid.uuid4())
    params = {"req_params": {"speaker": SPEAKER,
                             "audio_params": {"format": "mp3", "sample_rate": 24000, "speech_rate": RATE}}}
    ws.send(build(EV_START_SESSION, sid, json.dumps(params, ensure_ascii=False).encode()))
    next_msg(ws)
    ws.send(build(EV_TASK_REQUEST, sid, json.dumps({"req_params": {"text": text}}, ensure_ascii=False).encode()))
    ws.send(build(EV_FINISH_SESSION, sid, b"{}"))
    audio = bytearray()
    while True:
        m = next_msg(ws)
        if m is None or m["event"] == EV_SESSION_FINISHED:
            break
        if m["type"] == T_AUDIO_SERVER and m["payload"]:
            audio += m["payload"]
        elif m["event"] == EV_TTS_RESPONSE and m["payload"]:
            audio += m["payload"]
        elif m["type"] == T_ERROR:
            raise RuntimeError(m["payload"][:150].decode("utf-8", "replace"))
    try:
        ws.send(build(2, payload=b"{}"))
    except Exception:
        pass
    if not audio:
        raise RuntimeError("no audio")
    io.open(path, "wb").write(audio)
    return len(audio)


ok = fail = 0
for kind in ["pat", "angry", "legs", "dizzy"]:
    for i, text in enumerate(data.get("yukata." + kind, []), 1):
        for base in ("line_yukata_%s_%d" % (kind, i), "cus_yukata_%s" % fnv(text)):
            try:
                n = synth(text, os.path.join(VOICE, base + ".mp3"))
                ok += 1
                print("OK  %-30s %6dB  %s" % (base, n, text))
            except Exception as e:
                fail += 1
                print("FAIL %-29s %s" % (base, e))
            time.sleep(0.15)

SYS = {"yukata.done": "yukata_done", "yukata.full": "yukata_full", "yukata.sad": "yukata_sad",
       "yukata.panel_low": "line_yukata_panel_low", "yukata.panel_high": "line_yukata_panel_high"}
for k, base in SYS.items():
    lines = data.get(k, [])
    if not lines:
        continue
    try:
        n = synth(lines[0], os.path.join(VOICE, base + ".mp3"))
        ok += 1
        print("OK  %-30s %6dB  %s" % (base, n, lines[0]))
    except Exception as e:
        fail += 1
        print("FAIL %-29s %s" % (base, e))
    time.sleep(0.15)

print("done ok=%d fail=%d speaker=%s rate=%d" % (ok, fail, SPEAKER, RATE))
