# -*- coding: utf-8 -*-
"""按代码审查结果修复 crab.ts / index.ts（纯字符串替换，不用正则模板）。"""
import io

CP = r"C:\Users\21674\.openclaw\extensions\wallet-monitor\src\crab.ts"
IP = r"C:\Users\21674\.openclaw\extensions\wallet-monitor\src\index.ts"

c = io.open(CP, encoding="utf-8").read()
i = io.open(IP, encoding="utf-8").read()
log = []


def once(s, old, new, tag):
    if old in s:
        return s.replace(old, new, 1), True
    log.append("MISS " + tag)
    return s, False


# ---- 1) notifyLow 用本地日期 ----
old1 = 'const today = new Date().toISOString().slice(0, 10);'
new1 = 'const _d = new Date();\n        const today = `${_d.getFullYear()}-${String(_d.getMonth() + 1).padStart(2, "0")}-${String(_d.getDate()).padStart(2, "0")}`;'
c, ok = once(c, old1, new1, "1 notifyLow 本地日期")
if ok:
    log.append("1 notifyLow 本地日期 OK")

# ---- 3) failCount 声明上移（先做，后面按行删） ----
lines = c.split("\n")
fi = None
for idx, ln in enumerate(lines):
    if ln.strip() == "let failCount = 0;":
        fi = idx
        break
if fi is None:
    log.append("MISS 3 failCount 声明")
else:
    del lines[fi]
    ai = None
    for idx, ln in enumerate(lines):
        if ln.strip() == "let lowBalance = false;":
            ai = idx
            break
    if ai is None:
        log.append("MISS 3 lowBalance 锚点")
    else:
        lines.insert(ai + 1, "    let failCount = 0;")
        log.append("3 failCount 上移 OK")
c = "\n".join(lines)

# ---- 2) F6 并入完成气泡 ----
lines = c.split("\n")
si = di = None
for idx, ln in enumerate(lines):
    if "/* F6:" in ln:
        si = idx
    if "sysText(\"done\"" in ln and si is not None and di is None:
        di = idx
if si is None or di is None or di <= si:
    log.append("MISS 2 F6 块")
else:
    done_line = lines[di].replace("+ d, 8000)", "+ d + spentNote, 8000)")
    block = [
        "      /* F6: 单次消耗偏高并入完成气泡（原来单独 say 会被下一句覆盖） */",
        '      const spentNote =',
        '        Number.isFinite(dNum) && dNum >= 1 ? "（这轮花得有点多：￥" + dNum.toFixed(2) + "）" : "";',
    ]
    lines[si:di] = block
    # done 行位置因插入而移动
    shift = len(block) - (di - si)
    lines[di + shift] = done_line
    log.append("2 F6 合并 OK")
c = "\n".join(lines)

# ---- 4) 本次消耗为 0 / 空 时显示 — ----
old4 = 'r.lastRunDelta === undefined ? "—" : "-" + r.lastRunDelta'
new4 = '!r.lastRunDelta || r.lastRunDelta === "0" ? "—" : "-" + r.lastRunDelta'
n4 = c.count(old4)
c = c.replace(old4, new4)
log.append("4 delta 显示 替换 %d 处" % n4)

# ---- 5) 趋势标题按实际条数 ----
old5 = 'return `\\n近7天${range} ${spark}（单日最高 ￥${max.toFixed(2)}）`;'
new5 = 'const days = vals.length;\n      return `\\n近${days}天${range} ${spark}（单日最高 ￥${max.toFixed(2)}）`;'
c, ok = once(c, old5, new5, "5 趋势标题")
if ok:
    log.append("5 趋势标题 OK")

# ---- 6) before_agent_run 兜底 ----
old6 = 'if (typeof anyApiEarly.on === "function") anyApiEarly.on("before_agent_run", onRunStart);'
new6 = (
    'if (typeof anyApiEarly.on === "function") {\n'
    '      anyApiEarly.on("before_agent_run", onRunStart);\n'
    '    } else if (typeof anyApiEarly.registerHook === "function") {\n'
    '      anyApiEarly.registerHook("before_agent_run", onRunStart, { name: "wallet-monitor-run-start" });\n'
    '    }'
)
i, ok = once(i, old6, new6, "6 启动 hook 兜底")
if ok:
    log.append("6 启动 hook 兜底 OK")

# ---- 7) writeState 返回布尔，set_settings 如实反馈 ----
i, ok = once(i, "function writeState(s: any) {", "function writeState(s: any): boolean {", "7a 签名")
if ok:
    log.append("7a writeState 签名 OK")
old_tail = '    writeFileSync(STATE_PATH, JSON.stringify(s), "utf8");\n  } catch {\n    /* 写不了就算了 */\n  }\n}'
new_tail = '    writeFileSync(STATE_PATH, JSON.stringify(s), "utf8");\n    return true;\n  } catch {\n    /* 写不了就算了 */\n    return false;\n  }\n}'
i, ok = once(i, old_tail, new_tail, "7b 返回值")
if ok:
    log.append("7b writeState 返回值 OK")

old7 = '          st.settings = next;\n          writeState(st);\n          return { ok: true };'
new7 = '          st.settings = next;\n          const saved = writeState(st);\n          return { ok: saved !== false };'
i, ok = once(i, old7, new7, "7c set_settings")
if ok:
    log.append("7c set_settings 反馈 OK")

io.open(CP, "w", encoding="utf-8", newline="").write(c)
io.open(IP, "w", encoding="utf-8", newline="").write(i)
print("\n".join(log))
print("--- done 行 repr ---")
for ln in c.split("\n"):
    if 'sysText("done"' in ln:
        print(repr(ln))
