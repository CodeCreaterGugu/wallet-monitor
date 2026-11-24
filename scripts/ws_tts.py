# -*- coding: utf-8 -*-
"""零依赖的火山 TTS WebSocket 客户端（手工实现 TLS + WebSocket + 二进制协议）。

用法：
  py ws_tts.py --key <X-Api-Key> --text "测试" --out test.mp3
"""
import argparse
import base64
import hashlib
import json
import os
import socket
import ssl
import struct
import sys
import uuid

HOST = "openspeech.bytedance.com"
PATH = "/api/v3/tts/bidirection"

# ---- 协议常量 ----
T_FULL_CLIENT = 0b0001
T_FULL_SERVER = 0b1001
T_AUDIO_SERVER = 0b1011
T_ERROR = 0b1111

FLAG_WITH_EVENT = 0b0100
FLAG_LAST_NO_SEQ = 0b0010

EV_START_CONN = 1
EV_FINISH_CONN = 2
EV_CONN_STARTED = 50
EV_CONN_FAILED = 51
EV_CONN_FINISHED = 52
EV_START_SESSION = 100
EV_FINISH_SESSION = 102
EV_SESSION_STARTED = 150
EV_SESSION_FINISHED = 152
EV_SESSION_FAILED = 153
EV_TASK_REQUEST = 200
EV_TTS_RESPONSE = 352


class WS:
    def __init__(self, host, path, headers, timeout=20):
        raw = socket.create_connection((host, 443), timeout=timeout)
        ctx = ssl.create_default_context()
        self.sock = ctx.wrap_socket(raw, server_hostname=host)
        key = base64.b64encode(os.urandom(16)).decode()
        req = [
            f"GET {path} HTTP/1.1",
            f"Host: {host}",
            "Upgrade: websocket",
            "Connection: Upgrade",
            f"Sec-WebSocket-Key: {key}",
            "Sec-WebSocket-Version: 13",
        ]
        for k, v in headers.items():
            req.append(f"{k}: {v}")
        req.append("")
        req.append("")
        self.sock.sendall("\r\n".join(req).encode())

        buf = b""
        while b"\r\n\r\n" not in buf:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise ConnectionError("handshake closed")
            buf += chunk
        head, _, rest = buf.partition(b"\r\n\r\n")
        first = head.split(b"\r\n")[0].decode("latin-1")
        if "101" not in first:
            raise ConnectionError("handshake failed: " + first)
        self.buf = rest

    def send(self, data: bytes):
        mask = os.urandom(4)
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
        n = len(data)
        if n < 126:
            hdr = struct.pack("!BB", 0x82, 0x80 | n)
        elif n < 65536:
            hdr = struct.pack("!BBH", 0x82, 0x80 | 126, n)
        else:
            hdr = struct.pack("!BBQ", 0x82, 0x80 | 127, n)
        self.sock.sendall(hdr + mask + masked)

    def _recv_exact(self, n):
        while len(self.buf) < n:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise ConnectionError("closed")
            self.buf += chunk
        out, self.buf = self.buf[:n], self.buf[n:]
        return out

    def recv(self) -> bytes:
        b1, b2 = self._recv_exact(2)
        opcode = b1 & 0x0F
        length = b2 & 0x7F
        if length == 126:
            length = struct.unpack("!H", self._recv_exact(2))[0]
        elif length == 127:
            length = struct.unpack("!Q", self._recv_exact(8))[0]
        masked = b2 & 0x80
        mask = self._recv_exact(4) if masked else None
        payload = self._recv_exact(length)
        if mask:
            payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        if opcode == 0x8:
            raise ConnectionError("server closed")
        if opcode == 0x9:  # ping
            return b""
        return payload


def build(event, session_id="", payload=b"", msg_type=T_FULL_CLIENT):
    header = bytes([
        (1 << 4) | 1,
        (msg_type << 4) | FLAG_WITH_EVENT,
        (1 << 4) | 0,
        0,
    ])
    out = header + struct.pack(">i", event)
    # 连接级事件不带 session id
    if event not in (EV_START_CONN, EV_FINISH_CONN, EV_CONN_STARTED, EV_CONN_FAILED, EV_CONN_FINISHED):
        sid = session_id.encode()
        out += struct.pack(">I", len(sid)) + sid
    out += struct.pack(">I", len(payload)) + payload
    return out


def parse(data):
    if len(data) < 4:
        return None
    b0, b1, b2 = data[0], data[1], data[2]
    header_size = (b0 & 0x0F) * 4
    msg_type = b1 >> 4
    flag = b1 & 0x0F
    pos = header_size
    ev = None
    sid = ""
    if flag == FLAG_WITH_EVENT and len(data) >= pos + 4:
        ev = struct.unpack(">i", data[pos:pos + 4])[0]
        pos += 4
        if ev not in (EV_START_CONN, EV_CONN_STARTED, EV_CONN_FAILED, EV_CONN_FINISHED):
            if len(data) >= pos + 4:
                n = struct.unpack(">I", data[pos:pos + 4])[0]
                pos += 4
                sid = data[pos:pos + n].decode("utf-8", "replace")
                pos += n
        else:
            # 连接事件带 connect_id
            if len(data) >= pos + 4:
                n = struct.unpack(">I", data[pos:pos + 4])[0]
                pos += 4
                pos += n
    payload = b""
    if msg_type == T_ERROR:
        # 错误帧：4 字节 error_code + payload
        if len(data) >= pos + 4:
            code = struct.unpack(">I", data[pos:pos + 4])[0]
            pos += 4
            if len(data) >= pos + 4:
                n = struct.unpack(">I", data[pos:pos + 4])[0]
                pos += 4
                payload = data[pos:pos + n]
            return {"type": msg_type, "event": None, "session": "", "payload": payload, "error_code": code}
        return {"type": msg_type, "event": None, "session": "", "payload": b""}
    if len(data) >= pos + 4:
        n = struct.unpack(">I", data[pos:pos + 4])[0]
        pos += 4
        payload = data[pos:pos + n]
    return {"type": msg_type, "event": ev, "session": sid, "payload": payload}


def next_msg(ws, label=""):
    """循环读帧，跳过 ping/空帧，直到拿到可解析的协议消息"""
    for _ in range(20):
        data = ws.recv()
        if not data:
            continue
        m = parse(data)
        if m:
            return m
        print("  [raw]", label, data[:32].hex())
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", required=True)
    ap.add_argument("--text", default="你好，今天也省着点花哦。")
    ap.add_argument("--speaker", default="zh_female_gaolengyujie_uranus_bigtts")
    ap.add_argument("--out", default="tts_test.mp3")
    ap.add_argument("--resource", default="seed-tts-2.0")
    args = ap.parse_args()

    headers = {
        "X-Api-Key": args.key,
        "X-Api-Resource-Id": args.resource,
        "X-Api-Connect-Id": str(uuid.uuid4()),
    }
    try:
        ws = WS(HOST, PATH, headers)
    except Exception as e:
        print("CONNECT_FAILED:", e)
        return 2

    ws.send(build(EV_START_CONN, payload=b"{}"))
    m = next_msg(ws, "StartConnection")
    print("after StartConnection:", m and m["event"])
    if not m or m["event"] != EV_CONN_STARTED:
        print("connection not started, abort")
        return 3

    sid = str(uuid.uuid4())
    params = {
        "req_params": {
            "speaker": args.speaker,
            "audio_params": {"format": "mp3", "sample_rate": 24000, "speech_rate": 0},
        }
    }
    ws.send(build(EV_START_SESSION, sid, json.dumps(params, ensure_ascii=False).encode()))
    print("after StartSession:", (next_msg(ws, "StartSession") or {}).get("event"))

    ws.send(build(EV_TASK_REQUEST, sid, json.dumps({"req_params": {"text": args.text}}, ensure_ascii=False).encode()))
    ws.send(build(EV_FINISH_SESSION, sid, b"{}"))

    audio = bytearray()
    while True:
        m = next_msg(ws, "stream")
        if m is None:
            break
        if m["event"] == EV_SESSION_FINISHED or m["type"] == T_FULL_SERVER and m["event"] == EV_SESSION_FINISHED:
            break
        if m["type"] == T_AUDIO_SERVER and m["payload"]:
            audio += m["payload"]
        elif m["event"] == EV_TTS_RESPONSE and m["payload"]:
            audio += m["payload"]
        elif m["type"] == T_ERROR:
            print("SERVER_ERROR payload:", m["payload"][:300])
            break
        elif m["event"] == EV_SESSION_FAILED:
            print("SESSION_FAILED payload:", m["payload"][:300])
            break

    if audio:
        open(args.out, "wb").write(audio)
        print("OK bytes=", len(audio), "->", args.out)
    else:
        print("NO_AUDIO")

    try:
        ws.send(build(EV_FINISH_CONN, payload=b"{}"))
        print("after FinishConnection:", (next_msg(ws, "FinishConnection") or {}).get("event"))
    except Exception:
        pass


if __name__ == "__main__":
    sys.exit(main())
