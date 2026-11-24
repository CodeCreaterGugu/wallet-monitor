# -*- coding: utf-8 -*-
"""生成鲸鱼五段问候的自定义语音：voice/cus_whale_{hash}.mp3

- 文本取自 lines-whale.txt 的 [whale.greet_*] 段
- 文件名与前端 customFor() 的 lineHash 规则一致（FNV-1a 32 位十六进制）
- 复用 scripts/ws_tts.py 里的协议实现，密钥从桌面 key 文件读取，不打印
"""
import io
import os
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ws_tts  # noqa: E402

PLUG = os.path.dirname(HERE)
VOICE = os.path.join(PLUG, "voice")
TXT = os.path.join(PLUG, "lines-whale.txt")
KEYFILE = r"C:\Users\21674\Desktop\重要文件\API KEY.txt"
SPEAKER = "ICL_uranus_zh_female_qinglenggaoya_tob"
RESOURCE = "seed-tts-2.0"
RATE = 0


def read_audio_key():
    lines = io.open(KEYFILE, encoding="utf-8", errors="replace").read().splitlines()
    for i, ln in enumerate(lines):
        if ln.strip().rstrip("：:") == "audio":
            for nxt in lines[i + 1:]:
                s = nxt.strip()
                if not s:
                    continue
                if s.lower().startswith("api:"):
                    return s.split(":", 1)[1].strip()
                if s.lower().startswith("curl:"):
                    continue
                return s
    raise SystemExit("找不到 audio 密钥")


def fnv1a(text):
    h = 0x811C9DC5
    for b in text.encode("utf-8"):
        h ^= b
        h = (h * 0x01000193) & 0xFFFFFFFF
    return "%08x" % h


def synth(key, text, out_path):
    headers = {
        "X-Api-Key": key,
        "X-Api-Resource-Id": RESOURCE,
        "X-Api-Connect-Id": str(uuid.uuid4()),
    }
    ws = ws_tts.WS(ws_tts.HOST, ws_tts.PATH, headers)
    ws.send(ws_tts.build(ws_tts.EV_START_CONN, payload=b"{}"))
    m = ws_tts.next_msg(ws, "StartConnection")
    if not m or m["event"] != ws_tts.EV_CONN_STARTED:
        ws.close() if hasattr(ws, "close") else None
        return None

    sid = str(uuid.uuid4())
    params = {
        "req_params": {
            "speaker": SPEAKER,
            "audio_params": {"format": "mp3", "sample_rate": 24000, "speech_rate": RATE},
        }
    }
    ws.send(ws_tts.build(ws_tts.EV_START_SESSION, sid,
                         __import__("json").dumps(params, ensure_ascii=False).encode()))
    ws_tts.next_msg(ws, "StartSession")
    ws.send(ws_tts.build(ws_tts.EV_TASK_REQUEST, sid,
                         __import__("json").dumps({"req_params": {"text": text}},
                                                 ensure_ascii=False).encode()))
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
            print("  server error:", m["payload"][:200])
            break
    try:
        ws.send(ws_tts.build(ws_tts.EV_FINISH_CONN, payload=b"{}"))
    except Exception:
        pass
    if not audio:
        return None
    with open(out_path, "wb") as f:
        f.write(audio)
    return len(audio)


def main():
    secs, cur = {}, None
    for raw in io.open(TXT, encoding="utf-8").read().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            cur = line[1:-1]
            secs[cur] = []
            continue
        if cur and cur.startswith("whale.greet"):
            secs[cur].append(line)

    todo = []
    for kind in ["greet_morning", "greet_noon", "greet_afternoon", "greet_evening", "greet_night"]:
        for ln in secs.get("whale." + kind, []):
            name = "cus_whale_%s.mp3" % fnv1a(ln)
            path = os.path.join(VOICE, name)
            if os.path.exists(path) and os.path.getsize(path) > 2000:
                continue
            todo.append((kind, ln, name, path))

    print("待生成 %d 句" % len(todo))
    if not todo:
        return

    key = read_audio_key()
    ok = fail = 0
    for kind, ln, name, path in todo:
        try:
            n = synth(key, ln, path)
        except Exception as e:
            n = None
            print("  err", kind, repr(e)[:120])
        if n:
            ok += 1
            print("OK   %-18s %6d B  %s" % (kind, n, ln))
        else:
            fail += 1
            print("FAIL %-18s %s" % (kind, ln))
    print("完成：成功 %d，失败 %d" % (ok, fail))


if __name__ == "__main__":
    main()
