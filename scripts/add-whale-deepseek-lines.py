# -*- coding: utf-8 -*-
"""鲸鱼致敬 DeepSeek 台词：加 3 句 idle + 1 句 pat，并只给新 pat 句生成语音。"""
import io
import json
import os
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ws_tts  # noqa: E402

D = r"C:\Users\21674\.openclaw\extensions\wallet-monitor"
TXT = os.path.join(D, "lines-whale.txt")
VOICE = os.path.join(D, "voice")
KEYFILE = r"C:\Users\21674\Desktop\重要文件\API KEY.txt"
SPEAKER = "ICL_uranus_zh_female_qinglenggaoya_tob"
RATE = 15

IDLE_ADD = [
    "深海里有条蓝鲸，叫 DeepSeek。",
    "大肥鱼？……叫谁呢。",
    "听说它开源的那片海，比想象中深。",
]
PAT_ADD = "别摸，我不是那条大肥鱼。"


def fnv1a(t):
    h = 0x811C9DC5
    for b in t.encode("utf-8"):
        h ^= b
        h = (h * 0x01000193) & 0xFFFFFFFF
    return "%08x" % h


def read_key():
    for i, ln in enumerate(io.open(KEYFILE, encoding="utf-8", errors="replace").read().splitlines()):
        if ln.strip().rstrip("：:") == "audio":
            for nxt in io.open(KEYFILE, encoding="utf-8", errors="replace").read().splitlines()[i + 1:]:
                s = nxt.strip()
                if not s:
                    continue
                if s.lower().startswith("api:"):
                    return s.split(":", 1)[1].strip()
    raise SystemExit("no audio key")


def synth(key, text, out):
    ws = ws_tts.WS(ws_tts.HOST, ws_tts.PATH, {
        "X-Api-Key": key,
        "X-Api-Resource-Id": "seed-tts-2.0",
        "X-Api-Connect-Id": str(uuid.uuid4()),
    })
    ws.send(ws_tts.build(ws_tts.EV_START_CONN, payload=b"{}"))
    m = ws_tts.next_msg(ws, "StartConnection")
    if not m or m["event"] != ws_tts.EV_CONN_STARTED:
        return None
    sid = str(uuid.uuid4())
    p = {"req_params": {"speaker": SPEAKER, "audio_params": {"format": "mp3", "sample_rate": 24000, "speech_rate": RATE}}}
    ws.send(ws_tts.build(ws_tts.EV_START_SESSION, sid, json.dumps(p, ensure_ascii=False).encode()))
    ws_tts.next_msg(ws, "StartSession")
    ws.send(ws_tts.build(ws_tts.EV_TASK_REQUEST, sid, json.dumps({"req_params": {"text": text}}, ensure_ascii=False).encode()))
    ws.send(ws_tts.build(ws_tts.EV_FINISH_SESSION, sid, b"{}"))
    audio = bytearray()
    while True:
        m = ws_tts.next_msg(ws, "stream")
        if m is None:
            break
        if m["event"] == ws_tts.EV_SESSION_FINISHED:
            break
        if m["type"] == ws_tts.T_AUDIO_SERVER and m["payload"]:
            audio += m["payload"]
        elif m["event"] == ws_tts.EV_TTS_RESPONSE and m["payload"]:
            audio += m["payload"]
        elif m["type"] == ws_tts.T_ERROR or m["event"] == ws_tts.EV_SESSION_FAILED:
            print("  err:", m["payload"][:120])
            break
    try:
        ws.send(ws_tts.build(ws_tts.EV_FINISH_CONN, payload=b"{}"))
    except Exception:
        pass
    if not audio:
        return None
    io.open(out, "wb").write(bytes(audio))
    return len(audio)


s = io.open(TXT, encoding="utf-8").read()
changed = []

# idle 追加
if IDLE_ADD[0] not in s:
    marker = "雪地里踩一脚，咯吱咯吱的" if "雪地里踩一脚，咯吱咯吱的" in s else None
    # 鲸鱼 idle 段的最后一句
    lines = s.split("\n")
    # 找到 [whale.idle] 段
    start = None
    for i, ln in enumerate(lines):
        if ln.strip() == "[whale.idle]":
            start = i
            break
    if start is None:
        raise SystemExit("找不到 [whale.idle]")
    j = start + 1
    while j < len(lines) and not lines[j].startswith("["):
        j += 1
    insert_at = j
    while insert_at - 1 > start and not lines[insert_at - 1].strip():
        insert_at -= 1
    lines[insert_at:insert_at] = IDLE_ADD
    s = "\n".join(lines)
    changed.append("idle+3")

# pat 追加
if PAT_ADD not in s:
    lines = s.split("\n")
    start = None
    for i, ln in enumerate(lines):
        if ln.strip() == "[whale.pat]":
            start = i
            break
    if start is None:
        raise SystemExit("找不到 [whale.pat]")
    j = start + 1
    while j < len(lines) and not lines[j].startswith("["):
        j += 1
    insert_at = j
    while insert_at - 1 > start and not lines[insert_at - 1].strip():
        insert_at -= 1
    lines.insert(insert_at, PAT_ADD)
    s = "\n".join(lines)
    changed.append("pat+1")

io.open(TXT, "w", encoding="utf-8").write(s)
print("文本改动:", changed or "无（已存在）")

# 只给新 pat 句生成语音
name = "cus_whale_%s.mp3" % fnv1a(PAT_ADD)
out = os.path.join(VOICE, name)
if os.path.exists(out) and os.path.getsize(out) > 2000:
    print("语音已存在:", name)
else:
    n = synth(read_key(), PAT_ADD, out)
    print(("OK %s %d B  %s" % (name, n, PAT_ADD)) if n else "FAIL")
