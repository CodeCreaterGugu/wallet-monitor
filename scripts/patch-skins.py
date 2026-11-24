import io, re, sys

P = r"C:\Users\21674\.openclaw\extensions\wallet-monitor\src\crab.ts"
src = io.open(P, encoding="utf-8").read()
orig = src

# ---------- A. import ----------
if "from \"./skins.js\"" not in src:
    src = src.replace(
        'import { ICON_TALK } from "./crab-icon.js";',
        'import { ICON_TALK } from "./crab-icon.js";\nimport { SKINS, getSkin } from "./skins.js";',
        1,
    )

# ---------- B. LINES + pickLine -> module-level per-skin helpers ----------
start = src.index("const LINES: Array<[string, number]> = [")
end = src.index("function loadCfg()")
NEW_B = '''/* ===== 台词系统 =====
 * 优先级：lines-custom.txt > skins.ts 里该皮肤的台词 > 基础套装台词
 * 语音 key：line_pat_1 -> line_{皮肤}_pat_1（文件不存在自动回退）
 */
const CUSTOM_LINES: Record<string, string[]> = {};
const CUSTOM_SKIN_LINES: Record<string, Record<string, string[]>> = {};
const CUSTOM_RATE = 0.35;   /* 有自定义台词时，进入该状态说自定义的概率 */
let customLoaded = false;

/** 解析自定义台词文件：[动作] 全局生效；[皮肤.动作] 只对该皮肤生效 */
function parseCustomLines(raw: string) {
  let skin = "";
  let kind = "";
  for (const rawLine of raw.split(/\\r?\\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#") || line.startsWith("//")) continue;
    const m = /^\\[([^\\]]+)\\]$/.exec(line);
    if (m) {
      const parts = m[1].trim().toLowerCase().split(".");
      if (parts.length >= 2) {
        skin = parts[0];
        kind = parts[1];
      } else {
        skin = "";
        kind = parts[0];
      }
      continue;
    }
    if (!kind) continue;
    if (skin) {
      const bucket = CUSTOM_SKIN_LINES[skin] ?? (CUSTOM_SKIN_LINES[skin] = {});
      (bucket[kind] ?? (bucket[kind] = [])).push(line);
    } else {
      (CUSTOM_LINES[kind] ?? (CUSTOM_LINES[kind] = [])).push(line);
    }
  }
}

/** 命中自定义台词则返回文本，否则 null */
function customFor(kind: string, skin: string): string | null {
  const pool = (CUSTOM_SKIN_LINES[skin]?.[kind] ?? []).concat(CUSTOM_LINES[kind] ?? []);
  if (!pool.length || Math.random() > CUSTOM_RATE) return null;
  return pool[Math.floor(Math.random() * pool.length)];
}

function pickLine(prev: string | null, skin: string): string {
  const custom = customFor("idle", skin);
  if (custom) return custom;
  const meta = getSkin(skin);
  const list = meta.idle.length ? meta.idle : SKINS[0].idle;
  const total = list.reduce((s, [, w]) => s + w, 0);
  for (let attempt = 0; attempt < 5; attempt++) {
    let r = Math.random() * total;
    for (const [line, w] of list) {
      r -= w;
      if (r <= 0) {
        if (line !== prev) return line;
        break;
      }
    }
  }
  return list[0][0];
}

'''
src = src[:start] + NEW_B + src[end:]

# ---------- C. ACTION_LINES + actionLine ----------
c_start = src.index("/* E4: 每个互动动作的台词（随机一句） */")
c_end = src.index("/* 懒加载：按需向后端要音频")
NEW_C = '''/* 台词与语音：自定义 > 皮肤 > 基础款 */
    async function ensureCustomLines() {
      if (customLoaded) return;
      customLoaded = true;
      try {
        const r: any = await host?.invoke?.("get_custom_lines", {});
        if (r && r.ok === true && typeof r.text === "string") parseCustomLines(r.text);
      } catch {
        /* 忽略：没有自定义文件也能正常跑 */
      }
    }

    /** 语音 key 按皮肤改名；对应文件不存在则回退基础款 */
    function voiceKeyFor(key: string): string {
      if (!key) return "";
      const skin = resolveSkin();
      if (skin !== "none") {
        const cand = key.replace(/^line_/, "line_" + skin + "_");
        if (CRAB_VOICE_NAMES.includes(cand)) return cand;
      }
      return CRAB_VOICE_NAMES.includes(key) ? key : "";
    }

    function actionLine(kind: string): { text: string; audio: string } | null {
      const skin = resolveSkin();
      const custom = customFor(kind, skin);
      if (custom) return { text: custom, audio: "" };
      const meta = getSkin(skin);
      const arr = meta.actions?.[kind] ?? getSkin("none").actions?.[kind];
      if (!arr || !arr.length) return null;
      const [text, audio] = arr[Math.floor(Math.random() * arr.length)];
      return { text, audio: voiceKeyFor(audio) };
    }

    '''
src = src[:c_start] + NEW_C + src[c_end:]

# ---------- D. skinLabel ----------
old_label = '''      const m: Record<string, string> = {
        none: "默认",
        christmas: "圣诞",
        newyear: "新年",
        whale: "鲸鱼",
      };
      return m[cfg.skin] ?? "默认";'''
if old_label in src:
    src = src.replace(old_label, '      return getSkin(cfg.skin).label;', 1)
else:
    print("WARN: skinLabel block not found")

# ---------- E. skin strip options + thumb ----------
old_opt = '''        const OPTIONS: Array<[string, string]> = [
          ["auto", "自动"],
          ["none", "默认"],
          ["christmas", "圣诞"],
          ["whale", "鲸鱼"],
        ];'''
new_opt = '''        const OPTIONS: Array<[string, string]> = [["auto", "自动"]];
        for (const s of SKINS) OPTIONS.push([s.id, s.label]);'''
if old_opt in src:
    src = src.replace(old_opt, new_opt, 1)
else:
    print("WARN: OPTIONS block not found")

old_thumb = '          const thumbKey = val === "auto" || val === "none" ? "idle" : val;'
new_thumb = '          const thumbKey = val === "auto" ? "skinprev_none" : getSkin(val).thumb;'
if old_thumb in src:
    src = src.replace(old_thumb, new_thumb, 1)
else:
    print("WARN: thumbKey line not found")

# ---------- F. init: load custom lines ----------
if "void ensureCustomLines();" not in src:
    src = src.replace("let cfg = loadCfg();", "let cfg = loadCfg();\n    void ensureCustomLines();", 1)

# ---------- G. pickLine call sites ----------
src = src.replace("lastLine = pickLine(lastLine);", "lastLine = pickLine(lastLine, resolveSkin());")

io.open(P, "w", encoding="utf-8", newline="").write(src)
print("patched:", len(orig), "->", len(src), "bytes")
