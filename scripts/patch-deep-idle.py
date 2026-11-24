# -*- coding: utf-8 -*-
import io

p = r"C:\Users\21674\.openclaw\extensions\wallet-monitor\src\crab.ts"
s = io.open(p, encoding="utf-8").read()
log = []

old1 = '        const idleStates = ["idle", "settle", "sleep", "wave"];\n        const canSwitch = idleStates.indexOf(state) >= 0;'
new1 = '        /* 互动时都可以换装；只有跑任务（busy / think）时禁止 */\n        const canSwitch = state !== "busy" && state !== "think";'
if old1 in s:
    s = s.replace(old1, new1, 1); log.append("1 skin gate OK")
else:
    log.append("1 MISS skin gate")

old2 = '      if (hovering) return setState("wave");'
new2 = '      /* 深度待机（3 分钟 settle / 10 分钟 sleep）时，悬停不打招呼 */\n      if (hovering && Date.now() - lastAct <= SETTLE_AFTER_MS) return setState("wave");'
if old2 in s:
    s = s.replace(old2, new2, 1); log.append("2 sync hover OK")
else:
    log.append("2 MISS sync hover")

old3 = """    body.onmouseenter = () => {
      if (hoverOffTimer) {
        clearTimeout(hoverOffTimer);
        hoverOffTimer = null;
      }
      hovering = true;
      lastAct = Date.now();
      setEdgeExpanded(true);
      sync();
    };"""
new3 = """    body.onmouseenter = () => {
      if (hoverOffTimer) {
        clearTimeout(hoverOffTimer);
        hoverOffTimer = null;
      }
      hovering = true;
      /* 深度待机中：悬停不刷新 lastAct，避免被拉回 idle */
      if (Date.now() - lastAct <= SETTLE_AFTER_MS) lastAct = Date.now();
      setEdgeExpanded(true);
      sync();
    };"""
if old3 in s:
    s = s.replace(old3, new3, 1); log.append("3 body hover OK")
else:
    log.append("3 MISS body hover")

old4 = """      hovering = true;
      lastAct = Date.now();
      setEdgeExpanded(true);
      sync();
    };
    talkBtn.onmouseleave = () => {"""
new4 = """      hovering = true;
      if (Date.now() - lastAct <= SETTLE_AFTER_MS) lastAct = Date.now();
      setEdgeExpanded(true);
      sync();
    };
    talkBtn.onmouseleave = () => {"""
if old4 in s:
    s = s.replace(old4, new4, 1); log.append("4 talkBtn hover OK")
else:
    log.append("4 MISS talkBtn hover")

io.open(p, "w", encoding="utf-8").write(s)
print("\n".join(log))
