# -*- coding: utf-8 -*-
"""通用：备份某套语音并用火山音色重做。

用法：py rebuild-skin-speaker.py --skin yukata --speaker ICL_uranus_zh_female_tianmeijiaoqiao_tob --rate 15 --backup-dir "D:\\AI生成\\语音\\和服_甜美桃子备份"
"""
import argparse
import io
import json
import os
import re
import shutil
import sys
import time
import uuid

D = r"C:\Users\21674\.openclaw\extensions\wallet-monitor"
VOICE = os.path.join(D, "voice")
sys.path.insert(0, os.path.join(D, "scripts"))
from ws_tts import (WS, build, next_msg, HOST, PATH, EV_START_CONN, EV_START_SESSION,
                    EV_FINISH_SESSION, EV_TASK_REQUEST, EV_SESSION_FINISHED,
                    EV_TTS_RESPONSE, T_AUDIO_SERVER, T_ERROR)

KEY_PATH = r"C:\Users\21674\Desktop\重要文件\API KEY.txt"

ap = argparse.ArgumentParser()
ap.add_argument("--skin", required=True)
ap.add_argument("--speaker", required=True)
ap.add_argument("--rate", type=int, default=0)
ap.add_argument("--backup-dir", required=True)
args = ap.parse_args()

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


def voice_names(skin, data):
    names = []
    for kind in ["pat", "angry", "legs", "dizzy"]:
        for i, text in enumerate(data.get("%s.%s" % (skin, kind), []), 1):
            if skin == "none":
                names.append("line_%s_%d" % (kind, i))
                names.append("cus_%s" % fnv(text))
            else:
                names.append("line_%s_%s_%d" % (skin, kind, i))
                names.append("cus_%s_%s" % (skin, fnv(text)))
    if skin == "none":
        names += ["done", "full", "sad", "line_panel_low", "line_panel_high"]
    else:
        names += ["%s_done" % skin, "%s_full" % skin, "%s_sad" % skin,
                  "line_%s_panel_low" % skin, "line_%s_panel_high" % skin]
    return names


TXT = os.path.join(D, "lines-%s.txt" % args.skin)
sec, data = None, {}
for ln in io.open(TXT, encoding="utf-8"):
    s = ln.strip()
    m = re.match(r"^\[([^\]]+)\]$", s)
    if m:
        sec = m.group(1)
        continue
    if sec and s and not s.startswith("#"):
        data.setdefault(sec, []).append(s)

names = voice_names(args.skin, data)

os.makedirs(args.backup_dir, exist_ok=True)
bk = 0
for n in names:
    for suffix in (".mp3", "_lq.mp3"):
        src = os.path.join(VOICE, n + suffix)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(args.backup_dir, n + suffix))
            bk += 1
print("backup:", bk, "->", args.backup_dir)


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
    params = {"req_params": {"speaker": args.speaker,
                             "audio_params": {"format": "mp3", "sample_rate": 24000, "speech_rate": args.rate}}}
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
    for i, text in enumerate(data.get("%s.%s" % (args.skin, kind), []), 1):
        base = ("line_%s_%d" % (kind, i)) if args.skin == "none" else ("line_%s_%s_%d" % (args.skin, kind, i))
        cus = ("cus_%s" % fnv(text)) if args.skin == "none" else ("cus_%s_%s" % (args.skin, fnv(text)))
        for b in (base, cus):
            try:
                n = synth(text, os.path.join(VOICE, b + ".mp3"))
                ok += 1
                print("OK  %-30s %6dB  %s" % (b, n, text))
            except Exception as e:
                fail += 1
                print("FAIL %-29s %s" % (b, e))
            time.sleep(0.15)

SYS = {"%s.done" % args.skin: ("done" if args.skin == "none" else "%s_done" % args.skin),
       "%s.full" % args.skin: ("full" if args.skin == "none" else "%s_full" % args.skin),
       "%s.sad" % args.skin: ("sad" if args.skin == "none" else "%s_sad" % args.skin),
       "%s.panel_low" % args.skin: ("line_panel_low" if args.skin == "none" else "line_%s_panel_low" % args.skin),
       "%s.panel_high" % args.skin: ("line_panel_high" if args.skin == "none" else "line_%s_panel_high" % args.skin)}
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

print("done ok=%d fail=%d skin=%s speaker=%s rate=%d" % (ok, fail, args.skin, args.speaker, args.rate))
