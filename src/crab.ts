import { createFeatureClient } from "openclaw/plugin-sdk/feature-contract";
import { contract } from "./contract.js";
import { CRAB_SPRITE_NAMES } from "./crab-images.js";
import { CRAB_IDLE } from "./crab-idle.js";
import { CRAB_VOICE_NAMES } from "./crab-voice.js";
import { ICON_TALK } from "./crab-icon.js";
import { SKINS, getSkin } from "./skins.js";

const POS_KEY = "wm-crab-pos";
const HIDDEN_KEY = "wm-crab-hidden";
const CFG_KEY = "wm-crab-cfg";
const NOTIFY_KEY = "wm-crab-notify";

/** 3 分钟无操作 → 坐下看书（比突然睡着自然） */
const SETTLE_AFTER_MS = 3 * 60 * 1000;
/** 30 分钟无操作 → 睡着 */
const SLEEP_AFTER_MS = 10 * 60 * 1000;
const LOW_BALANCE = 10;

type State =
  | "idle"
  | "settle"
  | "wave"
  | "sleep"
  | "low"
  | "talk"
  | "busy"
  | "cheer"
  | "christmas"
  | "full"
  | "error"
  | "think"
  | "shy"
  | "drag"
  | "stretch"
  | "yawn"
  | "scratch"
  | "checkwatch"
  | "greet_morning"
  | "greet_noon"
  | "greet_afternoon"
  | "greet_evening"
  | "greet_night"
  | "pat_happy"
  | "angry"
  | "dizzy";

type Cfg = { sound: boolean; budget: number; quiet: boolean; skin: string; threshold: number; volume: number; muted: boolean; opacity: number };

/* ===== 台词系统 =====
 * 优先级：lines-custom.txt > skins.ts 里该皮肤的台词 > 基础套装台词
 * 语音 key：line_pat_1 -> line_{皮肤}_pat_1（文件不存在自动回退）
 */
const CUSTOM_LINES: Record<string, Array<{ text: string; idx: number }>> = {};
const CUSTOM_SKIN_LINES: Record<string, Record<string, Array<{ text: string; idx: number }>>> = {};
const CUSTOM_RATE = 1;   /* 说自定义台词的概率：1 = 只用 txt，内置台词仅作 txt 丢失时的保险 */
let customLoaded = false;

/** 解析自定义台词文件：[动作] 全局生效；[皮肤.动作] 只对该皮肤生效 */
function parseCustomLines(raw: string) {
  let skin = "";
  let kind = "";
  for (const rawLine of raw.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#") || line.startsWith("//")) continue;
    const m = /^\[([^\]]+)\]$/.exec(line);
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
      const arr = bucket[kind] ?? (bucket[kind] = []);
      arr.push({ text: line, idx: arr.length + 1 });
    } else {
      const arr = CUSTOM_LINES[kind] ?? (CUSTOM_LINES[kind] = []);
      arr.push({ text: line, idx: arr.length + 1 });
    }
  }
}

/** 文本 → 短哈希（与 scripts/gen-custom-voice.py 完全一致，用来绑定音频文件） */
function lineHash(text: string): string {
  const bytes = new TextEncoder().encode(text);
  let h = 0x811c9dc5;
  for (let i = 0; i < bytes.length; i++) {
    h ^= bytes[i];
    h = Math.imul(h, 0x01000193) >>> 0;
  }
  return h.toString(16).padStart(8, "0");
}

/** 命中自定义台词则返回文本，否则 null
 *  优先级：该皮肤的专属段（写了就只用它）> 通用段
 *  自定义句没有现成语音，按文本哈希找 voice/cus_{hash}.mp3，没有就静音 */
function customFor(kind: string, skin: string): { text: string; audio: string } | null {
  const own = CUSTOM_SKIN_LINES[skin]?.[kind];
  const pool = own && own.length ? own : (CUSTOM_LINES[kind] ?? []);
  if (!pool.length || Math.random() > CUSTOM_RATE) return null;
  const pick = pool[Math.floor(Math.random() * pool.length)];
  const hash = lineHash(pick.text);
  /* 优先用“文本指纹”音频（改字自动换文件）；
   * 该文件没生成 / 加载失败时，回退到按序号命名的 line_{皮肤}_{动作}_{n}.mp3 */
  const cusKey = skin && skin !== "none" ? "cus_" + skin + "_" + hash : "cus_" + hash;
  const seqKey = skin && skin !== "none" ? "line_" + skin + "_" + kind + "_" + pick.idx : "line_" + kind + "_" + pick.idx;
  /* 优先用序号音频（已在构建清单里，能保证发得出去）；
   * 序号文件不存在时（比如新增了第 4 句）才退回文本指纹音频 */
  const audio = CRAB_VOICE_NAMES.includes(seqKey) ? seqKey : cusKey;
  return { text: pick.text, audio };
}

function pickLine(prev: string | null, skin: string, kind: string = "idle"): string {
  const custom = customFor(kind, skin);
  if (custom) return custom.text;
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

function loadCfg(): Cfg {
  try {
    const c = JSON.parse(localStorage.getItem(CFG_KEY) || "null");
    if (c && typeof c === "object") {
      return {
        sound: c.sound !== false,
        budget: Number(c.budget) > 0 ? Number(c.budget) : 5,
        quiet: c.quiet !== false,
        skin: typeof c.skin === "string" ? c.skin : "auto",
        threshold: Number(c.threshold) > 0 ? Number(c.threshold) : 10,
        volume: Number.isFinite(Number(c.volume)) ? Math.min(1, Math.max(0, Number(c.volume))) : 0.8,
        muted: c.muted === true,
        opacity: Number.isFinite(Number(c.opacity)) ? Math.min(1, Math.max(0.05, Number(c.opacity))) : 1,
      };
    }
  } catch {
    /* 忽略 */
  }
  return { sound: true, budget: 5, quiet: true, skin: "auto", threshold: 10, volume: 0.8, muted: false, opacity: 1 };
}

/** 后端同步钩子：由 mountCrab 注入，把设置写进 state.json（localStorage 只是缓存） */
let syncCfgBackend: ((c: Cfg) => void) | null = null;

function saveCfg(c: Cfg) {
  try {
    localStorage.setItem(CFG_KEY, JSON.stringify(c));
  } catch {
    /* 忽略 */
  }
  try {
    syncCfgBackend?.(c);
  } catch {
    /* 忽略 */
  }
}

/** DeepSeek 高峰时段（北京时间，工作日 09-12 / 14-18） */
/* 中国法定节假日（2026，可自行增删；格式 YYYY-MM-DD） */
const HOLIDAYS = new Set<string>([
  // 元旦
  "2026-01-01", "2026-01-02", "2026-01-03",
  // 春节
  "2026-02-16", "2026-02-17", "2026-02-18", "2026-02-19", "2026-02-20", "2026-02-21", "2026-02-22",
  // 清明
  "2026-04-04", "2026-04-05", "2026-04-06",
  // 劳动节
  "2026-05-01", "2026-05-02", "2026-05-03", "2026-05-04", "2026-05-05",
  // 端午
  "2026-06-19", "2026-06-20", "2026-06-21",
  // 中秋
  "2026-09-25", "2026-09-26", "2026-09-27",
  // 国庆
  "2026-10-01", "2026-10-02", "2026-10-03", "2026-10-04",
  "2026-10-05", "2026-10-06", "2026-10-07", "2026-10-08",
]);

function isoToday(): string {
  const d = new Date();
  return d.getFullYear() + "-" +
    String(d.getMonth() + 1).padStart(2, "0") + "-" +
    String(d.getDate()).padStart(2, "0");
}

function isHolidayToday(): boolean {
  return HOLIDAYS.has(isoToday());
}

function isPeakNow(): boolean {
  const d = new Date();
  const day = d.getDay();
  const h = d.getHours();
  if (isHolidayToday()) return false;      /* 法定节假日按错峰算 */
  const weekday = day >= 1 && day <= 5;
  return weekday && ((h >= 9 && h < 12) || (h >= 14 && h < 18));
}

/** 深夜静音时段：23:00 - 06:00 */
function inQuietHours(): boolean {
  const h = new Date().getHours();
  return h >= 23 || h < 6;
}

export function mountCrab(host: any) {
  try {
    if (typeof document === "undefined") return;
    if (document.getElementById("wm-crab-root")) return;

    /* host 就是 control-ui 传进来的 feature client（提供 invoke / on） */
    const feature: any = host;

    /* 设置改存后端：localStorage 可能被清、被沙箱禁用，state.json 才是权威来源 */
    syncCfgBackend = (c: Cfg) => {
      try {
        void host?.invoke?.("set_settings", {
          sound: c.sound,
          budget: c.budget,
          quiet: c.quiet,
          skin: c.skin,
          threshold: c.threshold,
        });
      } catch {
        /* 忽略 */
      }
    };


    let cfg = loadCfg();
    void ensureCustomLines();
    /* 启动时先从后端拉一次，覆盖本地缓存（解决「设了又变回默认」） */
    void (async () => {
      try {
        const r: any = await host?.invoke?.("get_settings", {});
        if (!r || r.ok !== true) return;
        let changed = false;
        if (typeof r.sound === "boolean" && r.sound !== cfg.sound) {
          cfg.sound = r.sound;
          changed = true;
        }
        if (typeof r.budget === "number" && r.budget !== cfg.budget) {
          cfg.budget = r.budget;
          changed = true;
        }
        if (typeof r.quiet === "boolean" && r.quiet !== cfg.quiet) {
          cfg.quiet = r.quiet;
          changed = true;
        }
        if (typeof r.skin === "string" && r.skin !== cfg.skin) {
          cfg.skin = r.skin;
          changed = true;
        }
        if (typeof r.threshold === "number" && r.threshold !== cfg.threshold) {
          cfg.threshold = r.threshold;
          changed = true;
        }
        if (changed) {
          try {
            localStorage.setItem(CFG_KEY, JSON.stringify(cfg));
          } catch {
            /* 忽略 */
          }
          /* 读到后端设置后立刻应用（否则重启后服装不刷新） */
          try {
            applyImage();
            applyOpacity();
            sync();
          } catch {
            /* 忽略 */
          }
        }
      } catch {
        /* 忽略 */
      }
    })();

    /* ---------- 音效 ---------- */
    let ac: any = null;
    function audioCtx(): any {
      if (ac) return ac;
      try {
        const C = (window as any).AudioContext || (window as any).webkitAudioContext;
        ac = C ? new C() : null;
      } catch {
        ac = null;
      }
      return ac;
    }
    function beep(freq: number, dur = 0.08, type = "sine", gain = 0.05, delay = 0) {
      if (!cfg.sound) return;
      const a = audioCtx();
      if (!a) return;
      try {
        const o = a.createOscillator();
        const g = a.createGain();
        o.type = type;
        o.frequency.value = freq;
        o.connect(g);
        g.connect(a.destination);
        const t0 = a.currentTime + delay;
        g.gain.setValueAtTime(gain, t0);
        g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
        o.start(t0);
        o.stop(t0 + dur + 0.02);
      } catch {
        /* 忽略 */
      }
    }
    const playPop = () => beep(620, 0.07, "triangle", 0.05);
    const playChime = () => {
      beep(880, 0.12, "sine", 0.04, 0);
      beep(1320, 0.16, "sine", 0.028, 0.1);
    };

    /* ---------- 语音（懒加载，按需从后端取音频） ---------- */
    /* 音效：与语音可以同时播放，不走 currentVoice */
    let fxVoice: HTMLAudioElement | null = null;
    async function playFx(name: string) {
      if (!cfg.sound) return;
      if (!CRAB_VOICE_NAMES.includes(name)) return;
      try {
        if (fxVoice) {
          try {
            fxVoice.pause();
            fxVoice.currentTime = 0;
          } catch {
            /* 忽略 */
          }
        }
        const uri = await ensureVoice(name);
        if (!uri) return;
        const clone = new Audio(uri);
        clone.volume = Math.min(1, Math.max(0, cfg.volume));
        fxVoice = clone;
        void clone.play?.();
      } catch {
        /* 忽略 */
      }
    }

    /* 台词与语音：自定义 > 皮肤 > 基础款 */
    async function ensureCustomLines() {
      if (customLoaded) return;
      customLoaded = true;
      try {
        /* 全局文件 + 每套服装一个专属文件，后者覆盖前者 */
        const files = [
          "lines-custom.txt",
          "lines-none.txt",
          "lines-christmas.txt",
          "lines-whale.txt",
          "lines-yukata.txt",
        ];
        for (const f of files) {
          try {
            const r: any = await host?.invoke?.("get_custom_lines", { name: f });
            if (r && r.ok === true && typeof r.text === "string" && r.text.trim()) {
              parseCustomLines(r.text);
            }
          } catch {
            /* 单个文件失败不影响其他 */
          }
        }
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
      if (custom) return custom;
      const meta = getSkin(skin);
      const arr = meta.actions?.[kind] ?? getSkin("none").actions?.[kind];
      if (!arr || !arr.length) return null;
      const [text, audio] = arr[Math.floor(Math.random() * arr.length)];
      /* 这里只返回原始 key，皮肤前缀统一由 playVoice 处理，避免双重前缀 */
      return { text, audio };
    }

    /** 系统语音的文本（done / full / sad / panel_low / panel_high）
     *  皮肤专属 > 全局 > 代码内置 fallback；都没有则不出气泡 */
    function sysText(kind: string, fallback: string): string {
      const skin = resolveSkin();
      const pool = (CUSTOM_SKIN_LINES[skin]?.[kind] ?? []).concat(CUSTOM_LINES[kind] ?? []);
      if (!pool.length) return fallback;
      return pool[Math.floor(Math.random() * pool.length)].text;
    }

    /* 懒加载：缓存 data URI，每次播放新建 audio 元素，避免元素状态残留 */
    const voiceCache = new Map<string, string>();
    let currentVoice: HTMLAudioElement | null = null;
    let voiceSeq = 0;
    const VOICE_DEBUG = (() => {
      try {
        return window.localStorage.getItem("wm-voice-debug") === "1";
      } catch {
        return false;
      }
    })();

    async function ensureVoice(name: string): Promise<string | null> {
      const hit = voiceCache.get(name);
      if (hit) return hit;
      /* 先取高清版；若后端因体积过大报错，再取 _lq 低码率备用版 */
      const tries = name.endsWith("_lq") ? [name] : [name, name + "_lq"];
      for (const nm of tries) {
        try {
          const r: any = await host?.invoke?.("get_voice", { name: nm });
          if (r && r.ok === true && r.data) {
            const uri = "data:" + (r.mime || "audio/mpeg") + ";base64," + r.data;
            voiceCache.set(name, uri);
            if (VOICE_DEBUG) console.log("[wm-voice] loaded", nm, r.mime, String(r.data).length);
            return uri;
          }
        } catch {
          if (VOICE_DEBUG) console.warn("[wm-voice] error", nm);
        }
      }
      if (VOICE_DEBUG) console.warn("[wm-voice] miss", name);
      return null;
    }

    function stopCurrent() {
      if (!currentVoice) return;
      try {
        currentVoice.pause();
        currentVoice.currentTime = 0;
        currentVoice.muted = true;
      } catch {
        /* 忽略 */
      }
    }

    async function playVoice(name: string) {
      if (!cfg.sound) return;
      if (!name) return;
      const skin = resolveSkin();
      let key = name;
      /* cus_ 开头是自定义台词音频，构建清单里不会有，直接尝试读取 */
      if (!key.startsWith("cus_")) {
        /* 先试皮肤专用：line_pat_1 -> line_whale_pat_1；done -> whale_done */
        const cand =
          skin !== "none"
            ? key.startsWith("line_")
              ? key.replace(/^line_/, "line_" + skin + "_")
              : skin + "_" + key
            : key;
        if (cand !== key && CRAB_VOICE_NAMES.includes(cand)) {
          key = cand;
        } else if (!CRAB_VOICE_NAMES.includes(key)) {
          /* 皮肤专用语音还没生成：自动回退基础款 */
          const base = key.replace(/^line_[a-z0-9]+_/, "line_");
          if (!CRAB_VOICE_NAMES.includes(base)) return;
          key = base;
        }
      }
      const seq = ++voiceSeq;
      stopCurrent();
      const uri = await ensureVoice(key);
      if (!uri || seq !== voiceSeq) {
        if (VOICE_DEBUG) console.warn("[wm-voice] abort", key, !!uri, seq, voiceSeq);
        return;   /* 期间又被点了别的，放弃这次 */
      }
      const a = new Audio(uri);
      a.volume = Math.min(1, Math.max(0, cfg.volume));
      currentVoice = a;
      if (VOICE_DEBUG) console.log("[wm-voice] play", key);
      void a.play().catch(() => {
        setTimeout(() => {
          if (seq !== voiceSeq) return;
          try {
            a.currentTime = 0;
            void a.play().catch(() => {
              if (VOICE_DEBUG) console.warn("[wm-voice] play-blocked", key);
            });
          } catch {
            /* 忽略 */
          }
        }, 120);
      });
    }

    function speak(name: string) {
      void playVoice(name);
    }


    /* ---------- DOM ---------- */
    const root = document.createElement("div");
    root.id = "wm-crab-root";

    const badge = document.createElement("button");
    badge.type = "button";
    badge.className = "wm-crab-badge";
    badge.textContent = "🦀";
    badge.title = "点我找回螃蟹娘（Ctrl+Shift+U 也可以）";
    badge.hidden = true;

    const wrap = document.createElement("div");
    wrap.className = "wm-crab";

    let pos = { right: 22, bottom: 22 };
    try {
      const saved = JSON.parse(localStorage.getItem(POS_KEY) || "null");
      if (saved && typeof saved.right === "number" && typeof saved.bottom === "number") {
        pos = saved;
      }
    } catch {
      /* 忽略 */
    }
    wrap.style.right = pos.right + "px";
    wrap.style.bottom = pos.bottom + "px";

    const bubble = document.createElement("div");
    bubble.className = "wm-crab-bubble";
    bubble.hidden = true;

    const text = document.createElement("div");
    text.className = "wm-crab-text";

    const actions = document.createElement("div");
    actions.className = "wm-crab-actions";

    const mkBtn = (label: string, act: string) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "wm-crab-btn";
      b.dataset.act = act;
      b.textContent = label;
      return b;
    };
    const detailBtn = mkBtn("详情", "detail");
    actions.append(mkBtn("刷新", "refresh"), detailBtn, mkBtn("充值", "topup"), mkBtn("藏起来", "hide"));

    /* 大字余额（只在余额面板显示） */
    const bigNum = document.createElement("div");
    bigNum.className = "wm-crab-big";
    bigNum.hidden = true;

    /* A16: 近 14 天消耗热力图 */
    const heat = document.createElement("div");
    heat.className = "wm-crab-heat";
    heat.hidden = true;

    bubble.append(bigNum, heat, text, actions);

    const body = document.createElement("button");
    body.type = "button";
    body.className = "wm-crab-body";
    body.title = "点我～（右键设置）";

    const img = document.createElement("img");
    /* 立绘是 2 倍分辨率：按自然高度的一半显示，保证各状态比例一致 */
    /* 个别状态视觉偏满，单独缩放 */
    const SPRITE_SCALE: Record<string, number> = { busy: 0.84, think: 0.84 };

    img.onload = () => {
      try {
        const h = img.naturalHeight || 0;
        if (h > 0) {
          const k = SPRITE_SCALE[eff(state)] ?? 1;
          img.style.height = Math.round((h / 2) * k) + "px";
        }
        applyOpacity();
    requestAnimationFrame(updateMirror);
      } catch {
        /* 忽略 */
      }
    };
    img.alt = "螃蟹娘";
    img.className = "wm-crab-img";
    img.alt = "";
    img.src = CRAB_IDLE;   /* 首帧同步用内嵌版，立即可见 */

    img.draggable = false;

    /* 交叉溶解用的上层旧图 */
    const ghost = document.createElement("img");
    ghost.className = "wm-crab-img wm-crab-ghost";
    ghost.alt = "";
    ghost.draggable = false;
    body.append(img, ghost);


    const talkBtn = document.createElement("button");
    talkBtn.type = "button";
    talkBtn.className = "wm-crab-talk";
    talkBtn.title = "查看余额";
    const talkImg = document.createElement("img");
    talkImg.src = ICON_TALK;
    talkImg.alt = "查看余额";
    talkImg.draggable = false;
    talkBtn.append(talkImg);

    wrap.append(bubble, body, talkBtn);
    root.append(wrap, badge);
    document.body.appendChild(root);

    /* ---------- 右键菜单：只放设置 ---------- */
    const menu = document.createElement("div");
    menu.className = "wm-crab-menu";
    menu.hidden = true;
    document.body.appendChild(menu);

    function closeMenu() {
      menu.hidden = true;
    }

    /* editBudget 自己渲染输入行时置 true，阻止点击处理器重建菜单 */
    let keepMenu = false;

    /* 按菜单真实尺寸把它限制在视口内（输入框面板比原来宽） */
    function clampMenu() {
      try {
        const w = menu.offsetWidth || 180;
        const h = menu.offsetHeight || 160;
        const curLeft = parseFloat(menu.style.left || "0");
        const curTop = parseFloat(menu.style.top || "0");
        const maxLeft = Math.max(8, window.innerWidth - w - 8);
        const maxTop = Math.max(8, window.innerHeight - h - 8);
        menu.style.left = Math.min(Math.max(8, curLeft), maxLeft) + "px";
        menu.style.top = Math.min(Math.max(8, curTop), maxTop) + "px";
      } catch {
        /* 忽略 */
      }
    }

    /* D7: 控制面板（开关 + 数字输入，替代纯文本菜单） */
    function rowSwitch(label: string, on: boolean, fn: () => void) {
      const row = document.createElement("div");
      row.className = "wm-crab-row";
      const sp = document.createElement("span");
      sp.textContent = label;
      const sw = document.createElement("button");
      sw.type = "button";
      sw.className = "wm-crab-sw" + (on ? " on" : "");
      sw.textContent = on ? "开" : "关";
      sw.onclick = (ev: Event) => {
        ev.stopPropagation();
        fn();
      };
      row.append(sp, sw);
      menu.append(row);
    }

    /* 面板里的数字项：只渲染输入框，统一由底部「保存」提交 */
    const pendingNum: Record<string, number> = {};
    function rowNumber(label: string, key: string, value: number) {
      const row = document.createElement("div");
      row.className = "wm-crab-row";
      const sp = document.createElement("span");
      sp.textContent = label;
      const inp = document.createElement("input");
      inp.type = "number";
      inp.className = "wm-crab-input";
      inp.min = "0";
      inp.step = "1";
      inp.value = String(value);
      inp.oninput = () => {
        const v = Number(inp.value);
        if (Number.isFinite(v) && v >= 0) pendingNum[key] = v;
      };
      const unit = document.createElement("span");
      unit.className = "wm-crab-unit";
      unit.textContent = "元";
      row.append(sp, inp, unit);
      menu.append(row);
    }

    /* 右键小菜单：只有「设置」和「藏起来」 */
    function buildMenu() {
      menu.innerHTML = "";
      keepMenu = true;

      const setBtn = document.createElement("button");
      setBtn.type = "button";
      setBtn.className = "wm-crab-hide";
      setBtn.textContent = "⚙️ 设置";
      setBtn.onclick = (ev: Event) => {
        ev.stopPropagation();
        buildSettings();
      };
      menu.append(setBtn);

      const hide = document.createElement("button");
      hide.type = "button";
      hide.className = "wm-crab-hide";
      hide.textContent = "🦀 藏起来";
      hide.onclick = (ev: Event) => {
        ev.stopPropagation();
        setVisible(false);
      };
      menu.append(hide);

      clampMenu();
    }


    function buildSettings() {
      menu.innerHTML = "";
      keepMenu = true;

      rowSwitch("🌙 深夜静音", cfg.quiet, () => {
        cfg.quiet = !cfg.quiet;
        saveCfg(cfg);
        buildSettings();
      });
      /* 装扮：缩略图选择 */
      (function skinStrip() {
        const row = document.createElement("div");
        row.className = "wm-crab-row wm-row-skin";
        const sp = document.createElement("span");
        sp.className = "wm-crab-skin-label";
        sp.textContent = "🎁 装扮：" + skinLabel();
        row.append(sp);
        menu.append(row);

        /* 互动时都可以换装；只有跑任务（busy / think）时禁止 */
        const canSwitch = state !== "busy" && state !== "think";

        const strip = document.createElement("div");
        /* 必须带 wm-row-skin：否则进入专注模式时它自己被隐藏 → 反复触发 mouseenter/leave → 闪烁 */
        strip.className = "wm-crab-skins wm-row-skin";

        /* 拖动装扮条时不要触发选装 */
        let stripDragged = false;
        const OPTIONS: Array<[string, string]> = [["auto", "自动"]];
        for (const s of SKINS) OPTIONS.push([s.id, s.label]);
        for (const [val, name] of OPTIONS) {
          const cell = document.createElement("button");
          cell.type = "button";
          cell.className = "wm-skin-cell";
          cell.title = name;
          /* 当前选中高亮 */
          const cur = cfg.skin === val || (val === "auto" && cfg.skin === "auto");
          if (cur) cell.classList.add("on");
          if (!canSwitch) {
            cell.disabled = true;
            cell.classList.add("disabled");
          }

          /* 自动 → 用默认立绘做缩略图 */
          const thumbKey = val === "auto" ? "skinprev_none" : getSkin(val).thumb;
          const im = document.createElement("img");
          void spriteSrc(thumbKey).then((u) => {
            if (u) im.src = u;
          });
          im.alt = name;
          im.draggable = false;

          const tag = document.createElement("span");
          tag.textContent = name;

          cell.append(im, tag);
          cell.onclick = (ev: Event) => {
            ev.stopPropagation();
            if (stripDragged) return;
            if (!canSwitch) return;
            /* 点击立即进入专注 */
            if (skinEnterTimer) {
              clearTimeout(skinEnterTimer);
              skinEnterTimer = null;
            }
            menu.classList.add("focus-skin");
            cfg.skin = val;
            saveCfg(cfg);
            try {
              void spriteSrc(eff("idle")).then((u) => {
                if (u) wipeTo(u);
              });
            } catch {
              /* 忽略 */
            }
            buildSettings();
          };
          strip.append(cell);
        }
        menu.append(strip);

        /* 装扮条：滚轮横向滚 + 鼠标拖动 */
        strip.addEventListener(
          "wheel",
          (ev: WheelEvent) => {
            const d = Math.abs(ev.deltaY) >= Math.abs(ev.deltaX) ? ev.deltaY : ev.deltaX;
            strip.scrollLeft += d;
            ev.preventDefault();
            ev.stopPropagation();
          },
          { passive: false },
        );
        let dragStartX = 0;
        let dragging = false;
        let dragMoved = 0;
        strip.addEventListener("pointerdown", (ev: PointerEvent) => {
          dragging = true;
          stripDragged = false;
          dragMoved = 0;
          dragStartX = ev.clientX;
          strip.classList.add("dragging");
        });
        strip.addEventListener("pointermove", (ev: PointerEvent) => {
          if (!dragging) return;
          const dx = ev.clientX - dragStartX;
          dragStartX = ev.clientX;
          if (dx === 0) return;
          strip.scrollLeft -= dx;
          dragMoved += Math.abs(dx);
          /* 超过 6px 才算“真的在拖”，否则保留点击能力 */
          if (dragMoved > 6) stripDragged = true;
        });
        const endStripDrag = () => {
          dragging = false;
          strip.classList.remove("dragging");
          if (stripDragged) {
            /* 拖动结束后紧接着的 click 要吞掉，稍后恢复 */
            setTimeout(() => {
              stripDragged = false;
            }, 80);
          }
        };
        strip.addEventListener("pointerup", endStripDrag);
        strip.addEventListener("pointercancel", endStripDrag);
        strip.addEventListener("pointerleave", () => {
          dragging = false;
          strip.classList.remove("dragging");
        });

        /* 悬停整条时进入专注模式，便于看服装 */
        /* 悬停满 1.5 秒才进入专注，避免鼠标扫过就触发 */
        let skinEnterTimer: any = null;
        let skinLeaveTimer: any = null;
        const enterSkin = () => {
          if (skinLeaveTimer) {
            clearTimeout(skinLeaveTimer);
            skinLeaveTimer = null;
          }
          if (skinEnterTimer) return;
          skinEnterTimer = setTimeout(() => {
            skinEnterTimer = null;
            menu.classList.add("focus-skin");
          }, 750);
        };
        const leaveSkin = () => {
          if (skinEnterTimer) {
            clearTimeout(skinEnterTimer);
            skinEnterTimer = null;
          }
          if (skinLeaveTimer) clearTimeout(skinLeaveTimer);
          skinLeaveTimer = setTimeout(() => {
            skinLeaveTimer = null;
            menu.classList.remove("focus-skin");
          }, 120);
        };
        strip.onmouseenter = enterSkin;
        strip.onmouseleave = leaveSkin;
        row.onmouseenter = enterSkin;
        row.onmouseleave = leaveSkin;

        if (!canSwitch) {
          const warn = document.createElement("div");
          warn.className = "wm-crab-warn";
          warn.textContent = "忙着写代码呢，晚点再说哟~";
          menu.append(warn);
        }
      })();

      rowNumber("⚠️ 告急阈值", "threshold", cfg.threshold);
      rowNumber("📊 今日预算", "budget", cfg.budget);

      /* 透明度滑条 */
      (function opacityRow() {
        const row = document.createElement("div");
        row.className = "wm-crab-row wm-row-opacity";
        const sp = document.createElement("span");
        sp.textContent = "👻 透明度";
        const range = document.createElement("input");
        range.type = "range";
        range.min = "0";
        range.max = "100";
        range.step = "5";
        range.className = "wm-crab-range";
        range.value = String(Math.round(cfg.opacity * 100));
        range.oninput = () => {
          cfg.opacity = Number(range.value) / 100;
          applyOpacity();
        };
        range.onchange = () => saveCfg(cfg);
        /* 拖动透明度时：其它内容+面板底色渐隐，便于看清角色 */
        range.onpointerdown = () => menu.classList.add("focus-opacity");
        range.onpointerup = () => menu.classList.remove("focus-opacity");
        range.onpointercancel = () => menu.classList.remove("focus-opacity");
        range.onmouseup = () => menu.classList.remove("focus-opacity");
        row.append(sp, range);
        menu.append(row);
      })();
      rowSwitch("🔊 音效", cfg.sound, () => {
        cfg.sound = !cfg.sound;
        saveCfg(cfg);
        buildSettings();
      });


      /* 音量滑条：拖动松开时播放一次提示音 */
      (function volumeRow() {
        const row = document.createElement("div");
        row.className = "wm-crab-row";
        const sp = document.createElement("span");
        sp.textContent = "🔊 音量";
        const range = document.createElement("input");
        range.type = "range";
        range.min = "0";
        range.max = "100";
        range.step = "5";
        range.className = "wm-crab-range";
        range.value = String(Math.round(cfg.volume * 100));
        /* 音效关闭时：滑条灰掉不可操作 */
        range.disabled = !cfg.sound;
        if (!cfg.sound) row.classList.add("dim");
        range.oninput = () => {
          pendingNum.volume = Number(range.value) / 100;
        };
        const test = () => {
          const v = Number(range.value) / 100;
          cfg.volume = v;
          saveCfg(cfg);
          if (v <= 0) return;   /* 音量 0 就不出声 */
          try {
            beep(880, 0.16, "sine", 0.06 * v, 0);
          } catch {
            /* 忽略 */
          }
        };
        range.onpointerup = test;
        range.onchange = test;
        row.append(sp, range);
        menu.append(row);
      })();

      /* 底部：居中保存 + 绿色成功提示 */
      const okHint = document.createElement("div");
      okHint.className = "wm-crab-okhint";
      okHint.textContent = "保存成功";
      okHint.hidden = true;

      const saveBtn = document.createElement("button");
      saveBtn.type = "button";
      saveBtn.className = "wm-crab-save";
      saveBtn.textContent = "保存";
      saveBtn.onclick = (ev: Event) => {
        ev.stopPropagation();
        if (typeof pendingNum.threshold === "number" && pendingNum.threshold > 0) {
          cfg.threshold = pendingNum.threshold;
        }
        if (typeof pendingNum.budget === "number" && pendingNum.budget >= 0) {
          cfg.budget = pendingNum.budget;
        }
        if (typeof pendingNum.volume === "number") {
          cfg.volume = Math.min(1, Math.max(0, pendingNum.volume));
        }
        saveCfg(cfg);
        sync();
        okHint.hidden = false;
        setTimeout(() => {
          okHint.hidden = true;
        }, 1600);
      };
      /* H5: 恢复默认设置 */
      const resetBtn = document.createElement("button");
      resetBtn.type = "button";
      resetBtn.className = "wm-crab-reset";
      resetBtn.textContent = "恢复默认";
      resetBtn.onclick = (ev: Event) => {
        ev.stopPropagation();
        cfg.sound = true;
        cfg.budget = 5;
        cfg.quiet = true;
        cfg.skin = "auto";
        cfg.threshold = 10;
        cfg.volume = 0.8;
        cfg.muted = false;
        cfg.opacity = 1;
        saveCfg(cfg);
        applyOpacity();
        applyImage();
        buildSettings();
      };
      menu.append(resetBtn);

      const ver = document.createElement("div");
      ver.className = "wm-crab-ver";
      ver.textContent = "版本 1.0.0";
      menu.append(saveBtn, okHint, ver);

      clampMenu();
    }

    function editBudget() {
      /* 用面板内输入框代替 window.prompt：Control UI 里 prompt 可能被沙箱拦掉，导致设了不生效 */
      keepMenu = true;
      menu.innerHTML = "";
      const row = document.createElement("div");
      row.className = "wm-crab-ask";

      const lab = document.createElement("span");
      lab.textContent = "今日预算 ¥";

      const inp = document.createElement("input");
      inp.type = "number";
      inp.min = "0";
      inp.step = "1";
      inp.className = "wm-crab-input";
      inp.value = String(cfg.budget);

      const ok = document.createElement("button");
      ok.type = "button";
      ok.className = "wm-crab-ok";
      ok.textContent = "保存";
      ok.onclick = (ev: Event) => {
        ev.stopPropagation();
        const n = Number(inp.value);
        if (!Number.isFinite(n) || n < 0) {
          say("预算要填个数字哦～", 5000);
          return;
        }
        cfg.budget = Math.round(n * 100) / 100;
        saveCfg(cfg);
        closeMenu();
        say(cfg.budget === 0 ? "好，不限预算～" : "记下了，今天预算 ¥" + cfg.budget, 6000);
      };

      row.append(lab, inp, ok);
      menu.append(row);
      /* 输入行比按钮宽，重新贴边一次 */
      clampMenu();
      setTimeout(() => {
        try {
          inp.focus();
          inp.select();
        } catch {
          /* 忽略 */
        }
      }, 30);
      return;
    }

    body.addEventListener("contextmenu", (e: MouseEvent) => {
      e.preventDefault();
      lastAct = Date.now();
      if (!menu.hidden) {
        closeMenu();
        return;
      }
      buildMenu();
      menu.style.left = e.clientX + "px";
      menu.style.top = e.clientY + "px";
      menu.hidden = false;
      clampMenu();
      playPop();
    });

    document.addEventListener(
      "mousedown",
      (e: MouseEvent) => {
        const t = e.target as Node;
        /* 余额面板：点面板外任意处就收起 */
        if (!bubble.hidden && !bubble.contains(t) && !talkBtn.contains(t)) {
          bubble.hidden = true;
          detailOpen = false;
          detailBtn.textContent = "详情";
          sync();
        }
        /* 右键菜单：点菜单外关闭 */
        if (!menu.hidden && !menu.contains(t)) closeMenu();
      },
      true,
    );

    document.addEventListener("keydown", (e: KeyboardEvent) => {
      if (e.key === "Escape" && !menu.hidden) closeMenu();
    });

    /* ---------- 状态机 ---------- */
    let state: State = "idle";

    /* 调试 HUD：localStorage 里 wm-debug=1 时，左下角显示当前状态与图片实际尺寸 */
    const DEBUG_HUD = (() => {
      try {
        return window.localStorage.getItem("wm-debug") === "1";
      } catch {
        return false;
      }
    })();
    let debugHud: HTMLDivElement | null = null;
    if (DEBUG_HUD) {
      debugHud = document.createElement("div");
      debugHud.className = "wm-debug-hud";
      document.body.appendChild(debugHud);
      setInterval(() => {
        try {
          const r = img.getBoundingClientRect();
          const k = eff(state);
          debugHud!.textContent =
            "state=" + state + "  sprite=" + k +
            "\nnatural=" + img.naturalWidth + "x" + img.naturalHeight +
            "  rendered=" + Math.round(r.width) + "x" + Math.round(r.height);
        } catch {
          /* 忽略 */
        }
      }, 500);
    }
    let hovering = false;
    let hoverOffTimer: any = null;
    let overTalkBtn = false;   /* 指针是否停在余额按钮上 */   /* 离开迟滞：避免立绘宽度变化导致进出反复触发 */
    let busy = false;
    /* ---- 新增状态计时器 ---- */
    let thinkSince = 0;          // 长任务开始时间，0 表示未运行
    let shyUntil = 0;
    let patUntil = 0;      // 摸头高兴持续到
    let angryUntil = 0;    // 生气持续到
    let dizzyUntil = 0;    // 眩晕持续到            // 害羞持续到
    let greetKind: State = "greet_morning";
    let greetUntil = 0;          // 问候持续到
    let greetDay = "";           // 最近问候日期
    let idleAct: State = "stretch";
    let idleActUntil = 0;        // 待机小动作持续到
    /* 气泡是不是「对话式」（true = 抢 talk 姿势）；待机小动作的伴随台词传 false */
    let speechBubble = true;
    /* 充值后的「吃饱」状态：最高优先级，持续 12 秒 */
    let refillUntil = 0;
    /* 任务完成后的欢呼，持续 2 秒（压过气泡） */
    let cheerUntil = 0;
    const BAL_KEY = "wm-crab-last-balance";
    let lastAct = Date.now();
    let lowBalance = false;
    let failCount = 0;
    let lowSpokeDay = "";
    let sessionSpent = 0;
    let notifyDeniedHinted = false;   /* G1: 本页面会话累计消耗 */   /* F2: 当天是否已提醒过余额 */
    let overBudget = false;

    /** 换装映射：圣诞装替换「待机」那一格 */
    /** 节日自动装扮 */
    function autoSkin(): string {
      const d = new Date();
      const m = d.getMonth() + 1;
      const day = d.getDate();
      if (m === 12 && day >= 20) return "christmas";
      /* 新年装已停用：与基础款差异太小 */
      return "none";
    }

    function resolveSkin(): string {
      return cfg.skin === "auto" ? autoSkin() : cfg.skin;
    }

    function skinLabel(): string {
      if (cfg.skin === "auto") {
        const r = autoSkin();
        if (r === "christmas") return "自动(圣诞)";
        if (r === "newyear") return "自动(新年)";
        return "自动";
      }
      return getSkin(cfg.skin).label;
    }

    function eff(s: State): string {
      const k = resolveSkin();
      if (s === "idle") {
        if (k !== "none") {
          if (CRAB_SPRITE_NAMES.includes(k + "_idle")) return k + "_idle";
          if (CRAB_SPRITE_NAMES.includes(k)) return k;
        }
      } else if (k !== "none") {
        /* 皮肤专属动作图：whale_busy / christmas_talk / whale_greet_night … */
        if (CRAB_SPRITE_NAMES.includes(k + "_" + s)) return k + "_" + s;
      }
      /* 中午/下午/晚上优先用自己的立绘，没有就复用相近的 */
      if (s === "greet_noon") {
        if (CRAB_SPRITE_NAMES.includes("greet_noon")) return "greet_noon";
        return CRAB_SPRITE_NAMES.includes("greet_morning") ? "greet_morning" : "wave";
      }
      if (s === "greet_afternoon") {
        if (CRAB_SPRITE_NAMES.includes("greet_afternoon")) return "greet_afternoon";
        return CRAB_SPRITE_NAMES.includes("greet_morning") ? "greet_morning" : "wave";
      }
      if (s === "greet_evening") {
        if (CRAB_SPRITE_NAMES.includes("greet_evening")) return "greet_evening";
        return CRAB_SPRITE_NAMES.includes("greet_night") ? "greet_night" : "wave";
      }
      return s;
    }

    let fadeTimer: any = null;
    let imgAnim: Animation | null = null;
    let skipNextFade = false;
    /* 交叉溶解（纯 CSS 关键帧）：旧图淡出 + 新图淡入 */
    /* 立绘懒加载：按需从后端取，内存缓存复用 */
    const spriteCache = new Map<string, string>();
    let spriteSeq = 0;
    async function spriteSrc(key: string): Promise<string | null> {
      const k = key && CRAB_SPRITE_NAMES.includes(key) ? key : "idle";
      const hit = spriteCache.get(k);
      if (hit) return hit;
      /* idle 用内嵌版本，进页面立即可见 */
      if (k === "idle") {
        spriteCache.set("idle", CRAB_IDLE);
        return CRAB_IDLE;
      }
      try {
        const r: any = await host?.invoke?.("get_sprite", { name: k });
        if (!r || r.ok !== true || !r.data) return spriteCache.get("idle") ?? null;
        const uri = "data:" + (r.mime || "image/webp") + ";base64," + r.data;
        spriteCache.set(k, uri);
        return uri;
      } catch {
        return spriteCache.get("idle") ?? null;
      }
    }

    /* 预解码：确保新图已就绪再切换，避免出现空白帧（白闪） */
    function preload(src: string): Promise<void> {
      return new Promise<void>((resolve) => {
        try {
          const im = new Image();
          im.onload = () => resolve();
          im.onerror = () => resolve();
          im.src = src;
          if (typeof (im as any).decode === "function") {
            (im as any).decode().then(() => resolve()).catch(() => resolve());
          }
        } catch {
          resolve();
        }
      });
    }

    function fadeTo(src: string) {
      if (!src) return;
      if (img.getAttribute("data-src") === src) return;
      if (skipNextFade) skipNextFade = false;
      const hasOld = !!img.getAttribute("data-src") && img.complete;

      void preload(src).then(() => {
        if (hasOld) {
          /* 旧图放到上层，保持不透明，稍后淡出 */
          ghost.src = img.getAttribute("src") || "";
          ghost.style.height = img.style.height || "";
          ghost.style.opacity = "1";
          ghost.style.zIndex = "2";
          img.style.zIndex = "1";
        }
        img.setAttribute("data-src", src);
        img.src = src;

        requestAnimationFrame(() => {
          try {
            if (hasOld) {
              ghost.animate([{ opacity: 1 }, { opacity: 0 }], {
                duration: 260,
                easing: "ease",
                fill: "forwards",
              });
            }
          } catch {
            /* 忽略 */
          }
        });
      });

      if (fadeTimer) clearTimeout(fadeTimer);
      fadeTimer = setTimeout(() => {
        try {
          ghost.style.opacity = "0";
          ghost.removeAttribute("src");
          ghost.style.zIndex = "1";
          img.style.zIndex = "";
        } catch {
          /* 忽略 */
        }
      }, 320);
    }

    /* 缓动移动（用于边缘吸附，非线性） */
    let snapRaf: number | null = null;
    function animateTo(targetRight: number, targetBottom: number, ms = 300) {
      try {
        if (snapRaf !== null) cancelAnimationFrame(snapRaf);
        const startR = parseInt(wrap.style.right || "22", 10);
        const startB = parseInt(wrap.style.bottom || "22", 10);
        const t0 = performance.now();
        const easeOutCubic = (t: number) => 1 - Math.pow(1 - t, 3);
        const step = (now: number) => {
          const p = Math.min(1, (now - t0) / ms);
          const k = easeOutCubic(p);
          wrap.style.right = Math.round(startR + (targetRight - startR) * k) + "px";
          wrap.style.bottom = Math.round(startB + (targetBottom - startB) * k) + "px";
          if (p < 1) {
            snapRaf = requestAnimationFrame(step);
          } else {
            snapRaf = null;
            try {
              localStorage.setItem(
                POS_KEY,
                JSON.stringify({ right: targetRight, bottom: targetBottom }),
              );
            } catch {
              /* 忽略 */
            }
          }
        };
        snapRaf = requestAnimationFrame(step);
      } catch {
        /* 忽略 */
      }
    }

    /* 换装：旧图向下滑出消失，同时新图从上往下滑入 */
    function wipeTo(src: string) {
      if (!src) return;
      if (img.getAttribute("data-src") === src) return;
      const hasOld = !!img.getAttribute("data-src") && img.complete;

      void preload(src).then(() => {
        if (hasOld) {
          ghost.src = img.getAttribute("src") || "";
          ghost.style.height = img.style.height || "";
          ghost.style.opacity = "1";     /* 旧图全程不透明 */
          ghost.style.zIndex = "1";
          img.style.zIndex = "2";
        }
        img.setAttribute("data-src", src);
        img.src = src;

        requestAnimationFrame(() => {
          try {
            imgAnim = img.animate(
              [
                { transform: "translateY(-32%)" },
                { transform: "translateY(0)" },
              ],
              { duration: 700, easing: "cubic-bezier(0.22, 1, 0.36, 1)", fill: "none" },
            );
          } catch {
            /* 忽略 */
          }
        });
      });

      if (fadeTimer) clearTimeout(fadeTimer);
      fadeTimer = setTimeout(() => {
        try {
          ghost.style.opacity = "0";
          ghost.removeAttribute("src");
          ghost.style.zIndex = "1";
          img.style.zIndex = "";
        } catch {
          /* 忽略 */
        }
      }, 760);
    }

    function applyImage() {
      const key = eff(state);
      const seq = ++spriteSeq;
      void (async () => {
        const src = await spriteSrc(key);
        if (!src || seq !== spriteSeq) return;   /* 期间又切了别的，放弃这次 */
        fadeTo(src);
      })();
    }

    /* 透明度：作用于整个角色容器（立绘 + 气泡 + 按钮 + 文字） */
    function applyOpacity() {
      try {
        const v = String(Math.min(1, Math.max(0.05, cfg.opacity)));
        wrap.style.opacity = v;
        img.style.opacity = "1";   /* 避免和容器透明度叠加 */
      } catch {
        /* 忽略 */
      }
    }

    function setState(s: State) {
      if (state === s) return;
      state = s;
      applyImage();
    }

    function baseState(): State {
      const idle = Date.now() - lastAct;
      if (idle > SLEEP_AFTER_MS) return "sleep";
      if (idle > SETTLE_AFTER_MS) return "settle";
      return "idle";
    }

    /* 深夜时段自动把音量调低一次（用户改回去就不再干预） */
    let quietVolKey = "";
    function maybeQuietVolume() {
      try {
        if (!cfg.quiet) return;
        if (!inQuietHours()) return;
        const d = new Date();
        const key = d.toDateString() + (d.getHours() < 6 ? "-early" : "-night");
        if (quietVolKey === key) return;
        quietVolKey = key;
        cfg.volume = 0.35;
        saveCfg(cfg);
      } catch {
        /* 忽略 */
      }
    }

    function sync() {
      /* 充值后「吃饱满足」最高优先，压过一切 */
      if (Date.now() < refillUntil) return setState("full");
      /* 任务完成后的欢呼，同样压过气泡 */
      /* 拖拽中：被鼠标拎起来。优先级最高（高于眩晕），拖动必须立即响应 */
      if (dragging && moved) return setState("drag");
      /* 眩晕（双击）：持续时间独立，避免被其它状态打断 */
      if (Date.now() < dizzyUntil) return setState("dizzy");
      /* 摸头高兴 */
      if (Date.now() < patUntil) return setState("pat_happy");
      /* 生气 */
      if (Date.now() < angryUntil) return setState("angry");
      /* 点腿害羞 */
      if (Date.now() < shyUntil) return setState("shy");
      if (Date.now() < cheerUntil) return setState("cheer");
      if (!bubble.hidden) {
        /* 只有「打开余额详情面板 + 余额告急」才用乞讨表情，其他一律说话 */
        if (detailOpen && lowBalance) return setState("low");
        /* 方案 A：待机小动作窗口内的伴随台词不抢姿势，立绘继续做动作 */
        if (Date.now() < idleActUntil && !speechBubble) return setState(idleAct);
        return setState("talk");
      }
      /* 长任务超过 60 秒 -> 思考 */
      if (busy && thinkSince > 0 && Date.now() - thinkSince > 60000) return setState("think");
      if (busy) return setState("busy");
      if (failCount > 0) return setState("error");
      /* 定时问候 */
      if (Date.now() < greetUntil) return setState(greetKind);
      /* 待机随机小动作 */
      if (Date.now() < idleActUntil) return setState(idleAct);
      /* 深度待机（3 分钟 settle / 10 分钟 sleep）时，悬停不打招呼 */
      if (hovering && Date.now() - lastAct <= SETTLE_AFTER_MS) return setState("wave");
      setState(baseState());
    }

    /* ---------- 数据 ---------- */
    let hideTimer: any = null;
    let data: any = null;
    let lastOkAt: number | null = null;
    let lastLine: string | null = null;
    let acted = false;
    let detailOpen = false;

    let typeTimer: any = null;

    function say(msg: string, autoHideMs = 6000, showActions = false, asSpeech = true) {
      speechBubble = asSpeech;
      /* 打字机：逐字显示 */
      if (typeTimer) clearInterval(typeTimer);
      text.textContent = "";
      let typed = 0;
      typeTimer = setInterval(() => {
        typed += 2;
        text.textContent = msg.slice(0, typed);
        if (typed >= msg.length) {
          clearInterval(typeTimer);
          typeTimer = null;
        }
      }, 16);
      bubble.hidden = false;
      bigNum.hidden = true;   /* 默认隐藏，面板渲染时再显示 */
      heat.hidden = true;
      actions.style.display = showActions && acted ? "flex" : "none";
      if (hideTimer) clearTimeout(hideTimer);
      hideTimer = setTimeout(() => {
        bubble.hidden = true;
        detailOpen = false;
        detailBtn.textContent = "详情";
        speechBubble = true;
        sync();
      }, autoHideMs);
      sync();
    }

    function staleNote(): string {
      if (!lastOkAt) return "";
      const min = Math.floor((Date.now() - lastOkAt) / 60000);
      return min >= 1 ? `\n（数据过期，${min} 分钟前）` : "";
    }

    const WEEKDAY = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"];

    /** 今天的日期与星期（北京时间） */
    function todayLabel(): string {
      const d = new Date();
      return `${d.getMonth() + 1}月${d.getDate()}日 ${WEEKDAY[d.getDay()]}`;
    }
    /** 价格时段提示：只说当前所处的区间 */
    function peakNote(): string {
      const d = new Date();
      const day = d.getDay();
      const h = d.getHours();
      const weekday = day >= 1 && day <= 5;
      if (isHolidayToday()) return "\n\uD83C\uDF89 法定节假日，全天错峰 5 折";
  if (!weekday) return "\n\uD83C\uDF19 周末全天错峰，价格 5 折";
      if (h >= 9 && h < 12) return "\n\u23F0 工作日高峰 09:00\u201312:00，价格翻倍";
      if (h >= 14 && h < 18) return "\n\u23F0 工作日高峰 14:00\u201318:00，价格翻倍";
      return "\n\uD83C\uDF19 现在错峰（工作日非高峰），价格 5 折";
    }

    /** 简版：只有余额 + 本次 */
    function brief(r: any): string {
      if (!r || !r.ok) {
        return "查询失败：" + (r?.error ?? "未知错误") + staleNote();
      }
      const t = Number(r.totalBalance ?? "0");
      const mood = t <= 10 ? "😰" : t <= 20 ? "🙂" : "😄";
      void mood;   /* 余额改由大字行展示，这里不再重复 */
      return (
        `本次 ${!r.lastRunDelta || r.lastRunDelta === "0" ? "—" : "-" + r.lastRunDelta}` +
        peakNote() +
        staleNote()
      );
    }

    /** A13: 按近 7 天平均消耗预测还能用几天 */
    function forecastDays(r: any): string {
      try {
        const bal = Number(r?.totalBalance ?? "0");
        const hist: Array<{ d: string; spent: number }> = Array.isArray(r?.history) ? r.history : [];
        const days = hist.slice(-7).filter((h) => Number(h.spent) > 0);
        if (!days.length || !Number.isFinite(bal)) return "";
        const avg = days.reduce((a, b) => a + Number(b.spent), 0) / days.length;
        if (avg <= 0.01) return "";
        const left = bal / avg;
        return "\n⏳ 按近期速度约可用 " + (left >= 99 ? "99+" : left.toFixed(1)) + " 天";
      } catch {
        return "";
      }
    }

    /* A14/A15：今日报告 + 近 7 天对比 */
    function isoOf(d: Date): string {
      const m2 = String(d.getMonth() + 1).padStart(2, "0");
      const d2 = String(d.getDate()).padStart(2, "0");
      return d.getFullYear() + "-" + m2 + "-" + d2;
    }
    function weekCompare(r: any): string {
      try {
        const hist: Array<{ d: string; spent: number }> = Array.isArray(r?.history) ? r.history : [];
        if (!hist.length) return "";
        const map = new Map(hist.map((h) => [h.d, Number(h.spent) || 0]));
        const now = new Date();
        const sum = (from: number) => {
          let total = 0;
          for (let i = from; i < from + 7; i++) {
            const d = new Date(now);
            d.setDate(d.getDate() - i);
            total += map.get(isoOf(d)) ?? 0;
          }
          return total;
        };
        const cur = sum(0);
        const prev = sum(7);
        if (cur <= 0 && prev <= 0) return "";
        let tail = "";
        if (prev > 0) {
          const pct = ((cur - prev) / prev) * 100;
          tail = "（较前 7 天 " + (pct >= 0 ? "+" : "") + pct.toFixed(0) + "%）";
        }
        return "\n📊 近 7 天 ￥" + cur.toFixed(2) + tail;
      } catch {
        return "";
      }
    }

    /** 详版：点「详情」才展开，含今日 */
    function detail(r: any): string {
      if (!r || !r.ok) {
        return "查询失败：" + (r?.error ?? "未知错误") + staleNote();
      }
      const spent = Number(r.todaySpent ?? "0");
      const over =
        cfg.budget > 0 && spent > cfg.budget
          ? `\n😭 今天超预算了（预算 ¥${cfg.budget}）`
          : "";
      return (
        `📅 ${todayLabel()}\n` +

        `充值 ¥${r.toppedUp ?? "—"} · 赠金 ¥${r.granted ?? "—"}\n` +
        `本次消耗 ${!r.lastRunDelta || r.lastRunDelta === "0" ? "—" : "-" + r.lastRunDelta}\n` +
        `今日消耗 ${r.todaySpent === undefined ? "—" : "-" + r.todaySpent}` +
        (cfg.budget > 0 ? `（预算 ¥${cfg.budget}）` : "（未设预算）") +
        over +
        weekCompare(r) +
        forecastDays(r) +
        (sessionSpent > 0 ? "\n🧮 本会话累计 -￥" + sessionSpent.toFixed(2) : "") +
        trendLine(r) +
        peakNote() +
        staleNote()
      );
    }

    /** 近 7 天消耗迷你柱状（用方块字符） */
    function trendLine(r: any): string {
      const hist = Array.isArray(r?.history) ? r.history : [];
      if (!hist.length) return "";
      const vals = hist.map((h: any) => Number(h.spent) || 0);
      const max = Math.max(...vals, 0.01);
      const blocks = "▁▂▃▄▅▆▇█";
      const spark = vals
        .map((v: number) => blocks[Math.min(7, Math.max(0, Math.round((v / max) * 7)))])
        .join("");
      const first = hist[0]?.d ?? "";
      const last = hist[hist.length - 1]?.d ?? "";
      const range = first && last ? `（${first.slice(5)} ~ ${last.slice(5)}）` : "";
      const days = vals.length;
      return `\n近${days}天${range} ${spark}（单日最高 ￥${max.toFixed(2)}）`;
    }

    function renderBubble(autoHideMs = 20000) {
      say(detailOpen ? detail(data) : brief(data), autoHideMs, true);
      /* 大字余额 */
      try {
        const raw = data && data.ok ? String(data.totalBalance ?? "") : "";
        const v = Number(raw);
        if (raw !== "" && Number.isFinite(v)) {
          const lab = document.createElement("span");
          lab.className = "wm-crab-big-label";
          lab.textContent = "余额";
          const num = document.createElement("span");
          num.className = "wm-crab-big-num";
          num.textContent = "￥" + v.toFixed(2);
          bigNum.innerHTML = "";
          bigNum.append(lab, num);
          bigNum.hidden = false;
        }
      } catch {
        /* 忽略 */
      }
      /* A16: 详情模式下显示近 14 天热力图 */
      try {
        if (detailOpen && data && data.ok && Array.isArray(data.history) && data.history.length) {
          const hist = data.history.slice(-14) as Array<{ d: string; spent: number }>;
          const max = Math.max.apply(null, hist.map((h) => Number(h.spent) || 0)) || 1;
          heat.innerHTML = "";
          for (const h of hist) {
            const cell = document.createElement("i");
            const v = Number(h.spent) || 0;
            const ratio = v / max;
            const lv = v <= 0 ? 0 : ratio < 0.25 ? 1 : ratio < 0.5 ? 2 : ratio < 0.75 ? 3 : 4;
            cell.dataset.level = String(lv);
            cell.title = h.d + "  花 -￥" + v.toFixed(2);
            heat.append(cell);
          }
          heat.hidden = false;
        } else {
          heat.hidden = true;
        }
      } catch {
        heat.hidden = true;
      }
      detailBtn.textContent = detailOpen ? "收起" : "详情";
    }

    /* ---------- 低余额通知 ---------- */
    function notifyLow(r: any) {
      try {
        if (cfg.quiet && inQuietHours()) return;
        if (!(r && r.ok)) return;
        const t = Number(r.totalBalance ?? "999");
        const _d = new Date();
        const today = `${_d.getFullYear()}-${String(_d.getMonth() + 1).padStart(2, "0")}-${String(_d.getDate()).padStart(2, "0")}`;
        const key = t <= 2 ? "crit" : t <= cfg.threshold ? "low" : null;
        if (!key) return;
        const st = JSON.parse(localStorage.getItem(NOTIFY_KEY) || "{}");
        if (st.day !== today) {
          st.day = today;
          st.low = false;
          st.crit = false;
        }
        if (st[key]) return;
        st[key] = true;
        localStorage.setItem(NOTIFY_KEY, JSON.stringify(st));
        if (typeof Notification !== "undefined" && Notification.permission === "granted") {
          new Notification("🦀 螃蟹娘提醒", {
            body: t <= 2 ? `余额只剩 ¥${t}，快停机了！` : `余额只剩 ¥${t}，要不要充点？`,
            silent: true,
          });
        }
      } catch {
        /* 忽略 */
      }
    }

    async function refresh(show = false) {
      try {
        const r = await feature.invoke("get_balance", {});
        data = r;
        if (r && r.ok) {
          failCount = 0;
          lastOkAt = Date.now();
          /* 检测充值：余额比上次多 → 触发「吃饱」 */
          try {
            const prev = Number(localStorage.getItem(BAL_KEY) || "0");
            const nowBal = Number(r.totalBalance ?? "0");
            if (prev > 0 && nowBal > prev + 0.01) {
              refillUntil = Date.now() + 12000;
              /* 只播一段：如果正在播面板语音，等它播完再说，不要中途打断成半句“还…” */
              const playFull = () => speak("full");
              const cur = currentVoice;
              if (cur && !cur.paused && !cur.ended && Number.isFinite(cur.duration)) {
                const wait = Math.max(0, (cur.duration - cur.currentTime) * 1000) + 200;
                setTimeout(playFull, Math.min(6000, wait));
              } else {
                setTimeout(playFull, 200);
              }
              say(sysText("full", "🦀 谢谢主人！我吃饱啦～"), 9000);
              playChime();
              setTimeout(() => sync(), 12300);
            }
            if (Number.isFinite(nowBal)) localStorage.setItem(BAL_KEY, String(nowBal));
          } catch {
            /* 忽略 */
          }
          lowBalance = Number(r.totalBalance ?? "999") <= cfg.threshold;
      /* F2: 跌破阈值当天主动开口一次 */
      try {
        const dayKey = new Date().toDateString();
        if (lowBalance && lowSpokeDay !== dayKey) {
          lowSpokeDay = dayKey;
          const bal = Number(r.totalBalance ?? "0");
          speak("sad");
          say(
            sysText(
              "sad",
              bal <= 5 ? "余额快见底了…记得充值哦" : "余额不太够了，要不要充一点？",
            ),
            9000,
          );
        }
      } catch {
        /* 忽略 */
      }
          overBudget = cfg.budget > 0 && Number(r.todaySpent ?? "0") > cfg.budget;
          notifyLow(r);
        }
        if (show) {
          acted = true;
          actions.style.display = "flex";
          renderBubble();
        } else {
          if (overBudget && bubble.hidden) {
            acted = false;
            actions.style.display = "none";
            say(`今天已经花了 ¥${data?.todaySpent}，超预算了…`, 10000);
          }
          sync();
        }
      } catch (e) {
        failCount += 1;
        if (show) say("查询出错了：" + String(e) + staleNote(), 10000);
        else sync();
      }
    }

    /* ---------- 朝向：靠右时镜像朝左 ---------- */
    function updateMirror() {
      try {
        const r = wrap.getBoundingClientRect();
        const centerX = r.left + r.width / 2;
        const onLeft = centerX <= window.innerWidth / 2;
        img.style.transform = onLeft ? "rotateY(180deg)" : "none";
        /* 气泡跟随镜像：人物在屏幕左半边时，气泡翻到右侧并水平镜像 */
        talkBtn.classList.toggle("wm-side-right", onLeft);
        /* 气泡在左半边时改为向右延伸 */
        wrap.classList.toggle("wm-on-left", onLeft);
      } catch {
        /* 忽略 */
      }
    }

    /* ---------- 显隐 ---------- */
    function setVisible(v: boolean) {
      wrap.style.display = v ? "flex" : "none";
      badge.hidden = v;
      try {
        localStorage.setItem(HIDDEN_KEY, v ? "0" : "1");
      } catch {
        /* 忽略 */
      }
    }

    let hiddenFlag = false;
    try {
      hiddenFlag = localStorage.getItem(HIDDEN_KEY) === "1";
    } catch {
      /* 忽略 */
    }
    setVisible(!hiddenFlag);
    try {
      const w0 = wrap.offsetWidth || 160;
      const h0 = wrap.offsetHeight || 200;
      const r0 = Math.min(Math.max(4, window.innerWidth - w0 - 6), Math.max(4, parseInt(wrap.style.right || "22", 10)));
      const b0 = Math.min(Math.max(4, window.innerHeight - h0 - 6), Math.max(4, parseInt(wrap.style.bottom || "22", 10)));
      wrap.style.right = r0 + "px";
      wrap.style.bottom = b0 + "px";
    } catch {
      /* 忽略 */
    }
    requestAnimationFrame(updateMirror);
    setTimeout(updateMirror, 300);

    badge.onclick = () => setVisible(true);

    const onKey = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.shiftKey && (e.key === "U" || e.key === "u")) {
        e.preventDefault();
        setVisible(wrap.style.display === "none");
      }
    };
    document.addEventListener("keydown", onKey);

    /* ---------- 交互 ---------- */
    /* 贴边收起：鼠标进入展开，离开 300ms 后再缩回（防抖） */
    let edgeTimer: any = null;
    function setEdgeExpanded(on: boolean) {
      try {
        if (on) {
          if (edgeTimer) {
            clearTimeout(edgeTimer);
            edgeTimer = null;
          }
          wrap.classList.add("wm-expanded");
        } else {
          if (edgeTimer) clearTimeout(edgeTimer);
          edgeTimer = setTimeout(() => {
            edgeTimer = null;
            wrap.classList.remove("wm-expanded");
          }, 300);
        }
      } catch {
        /* 忽略 */
      }
    }

    body.onmouseenter = () => {
      if (hoverOffTimer) {
        clearTimeout(hoverOffTimer);
        hoverOffTimer = null;
      }
      hovering = true;
      /* 深度待机中：悬停不刷新 lastAct，避免被拉回 idle */
      if (Date.now() - lastAct <= SETTLE_AFTER_MS) lastAct = Date.now();
      setEdgeExpanded(true);
      sync();
    };
    body.onmouseleave = () => {
      if (hoverOffTimer) clearTimeout(hoverOffTimer);
      hoverOffTimer = setTimeout(() => {
        hoverOffTimer = null;
        /* 指针已经移到余额按钮上：保持 wave + 展开，什么都不做 */
        if (overTalkBtn) return;
        hovering = false;
        setEdgeExpanded(false);
        sync();
      }, 260);
    };

    /* 悬停在余额按钮上也保持展开，否则会误触发缩回 */
    /* 悬停余额按钮：与悬停角色完全一致（展开 + wave 姿态） */
    talkBtn.onmouseenter = () => {
      overTalkBtn = true;
      if (hoverOffTimer) {
        clearTimeout(hoverOffTimer);
        hoverOffTimer = null;
      }
      hovering = true;
      if (Date.now() - lastAct <= SETTLE_AFTER_MS) lastAct = Date.now();
      setEdgeExpanded(true);
      sync();
    };
    talkBtn.onmouseleave = () => {
      overTalkBtn = false;
      if (hoverOffTimer) clearTimeout(hoverOffTimer);
      hoverOffTimer = setTimeout(() => {
        hoverOffTimer = null;
        hovering = false;
        setEdgeExpanded(false);
        sync();
      }, 260);
    };

    body.onclick = (ev: MouseEvent) => {
      lastAct = Date.now();
      /* 点在哪一区：上部=头、中部=身体、下部=腿 */
      /* 眩晕保护：转圈期间继续点击只会延长眩晕，不触发其它互动 */
      if (Date.now() < dizzyUntil) {
        /* 每次点击都把计时重置为 2 秒（不叠加），并重播摇摆 */
        dizzyUntil = Date.now() + 2000;
        dizzy();
        playPop();
        /* 每次点击：说一句眩晕台词（语音 + 气泡文字） */
        const lnDizzyClick = actionLine("dizzy");
        if (lnDizzyClick) {
          speak(lnDizzyClick.audio);
          say(lnDizzyClick.text, 3000, false);
        }
        lastAct = Date.now();
        sync();
        return;
      }

      let zone: "head" | "body" | "legs" = "body";
      try {
        const r = img.getBoundingClientRect();
        const rel = r.height > 0 ? (ev.clientY - r.top) / r.height : 0.5;
        zone = rel < 0.34 ? "head" : rel < 0.75 ? "body" : "legs";
      } catch {
        /* 忽略 */
      }
      /* 立即切换形象（不再等 300ms） */
      if (feedbackTimer) {
        clearTimeout(feedbackTimer);
        feedbackTimer = null;
      }
      playPop();
      const DUR = 2500;
      /* 关键：切换动作前先清掉其它反馈计时，否则旧状态会因优先级更高而遮蔽新状态 */
      patUntil = 0;
      angryUntil = 0;
      shyUntil = 0;
      dizzyUntil = 0;
      if (zone === "head") {
        /* 点头 -> 高兴（眯眼笑） */
        patHead();
        patUntil = Date.now() + DUR;
        const lnPat = actionLine("pat");
        if (lnPat) {
          speak(lnPat.audio);
          say(lnPat.text, 4000, false);
        } else {
          speak("pat");
        }
      } else if (zone === "legs") {
        /* 点腿 -> 害羞 */
        shyUntil = Date.now() + DUR;
        const lnLeg = actionLine("legs");
        if (lnLeg) {
          speak(lnLeg.audio);
          say(lnLeg.text, 4000, false);
        } else {
          speak("shy");
        }
      } else {
        /* 点身子 -> 生气：先瞬间换图，再 180° 翻转（模拟转身） */
        angryUntil = Date.now() + DUR;
        skipNextFade = true;   /* 转身动画已足够，不要叠加渐变 */
        const lnAng = actionLine("angry");
        if (lnAng) {
          speak(lnAng.audio);
          say(lnAng.text, 4500, false);
        } else {
          speak("angry");
        }
        /* 重启动画：先移除再强制重排，保证每次都能重新播放 */
        try {
          imgAnim?.cancel();
          imgAnim = null;
        } catch {
          /* 忽略 */
        }
        img.classList.remove("wm-turn");
        void img.offsetWidth;
        img.classList.add("wm-turn");
        setTimeout(() => img.classList.remove("wm-turn"), DUR);
      }
      sync();
      /* 几秒后自动切回常态 */
      setTimeout(() => sync(), DUR + 80);
      try {
        if (typeof Notification !== "undefined" && Notification.permission === "default") {
          void Notification.requestPermission();
        }
        audioCtx()?.resume?.();
      } catch {
        /* 忽略 */
      }
    };

    /* 💬 按钮：打开/关闭余额面板 */
    talkBtn.onclick = () => {
      lastAct = Date.now();
      playPop();
      if (!bubble.hidden) {
        bubble.hidden = true;
        detailOpen = false;
        detailBtn.textContent = "详情";
        sync();
        return;
      }
      acted = true;
      actions.style.display = "flex";
      /* 打开余额面板：低于阈值一句、高于阈值另一句
       * 充值后 12 秒内不播：避免把「到账」那句推掉（会听到半句「还…」） */
      if (Date.now() > refillUntil) {
        speak(lowBalance ? "line_panel_low" : "line_panel_high");
      }
      if (data) renderBubble();
      else {
        lastLine = pickLine(lastLine, resolveSkin());
        say(lastLine, 15000, true);
      }
      void refresh(true);
    };

    actions.onclick = (ev: MouseEvent) => {
      const t = ev.target as HTMLElement;
      const act = t?.dataset?.act;
      if (!act) return;
      lastAct = Date.now();
      playPop();
      if (act === "refresh") void refresh(true);
      else if (act === "detail") {
        /* 点一次展开，再点一次收起 */
        detailOpen = !detailOpen;
        acted = true;
        actions.style.display = "flex";
        renderBubble();
      } else if (act === "topup") {
        window.open("https://platform.deepseek.com/top_up", "_blank", "noopener");
      } else if (act === "hide") {
        setVisible(false);
      }
    };

    /* ---------- 拖拽 ---------- */
    /* ---------- 小动作：摸头 / 头晕 ---------- */
    let holdTimer: any = null;

    function patHead() {
      try {
        wrap.classList.add("wm-crab-pat");
        setTimeout(() => wrap.classList.remove("wm-crab-pat"), 900);
        speak("giggle");
      } catch {
        /* 忽略 */
      }
    }

    let dizzyTimer: any = null;
    function dizzy() {
      try {
        /* 先清掉上一次的移除计时，否则会在动画中途被打断 */
        if (dizzyTimer) {
          clearTimeout(dizzyTimer);
          dizzyTimer = null;
        }
        wrap.classList.remove("wm-crab-dizzy");
        void wrap.offsetWidth;          /* 强制重排，保证重播 */
        wrap.classList.add("wm-crab-dizzy");
        dizzyTimer = setTimeout(() => {
          dizzyTimer = null;
          wrap.classList.remove("wm-crab-dizzy");
        }, 1300);
      } catch {
        /* 忽略 */
      }
    }

    let dragging = false;
    let moved = false;
    let lastDragSync = 0;
    let dragW = 0;
    let dragH = 0;
    let startX = 0;
    let startY = 0;
    let startRight = 0;
    let startBottom = 0;

    body.addEventListener("pointerdown", (e: PointerEvent) => {
      /* 通知权限：必须在用户手势里申请 */
      try {
        if (typeof Notification !== "undefined" && Notification.permission === "default") {
          void Notification.requestPermission();
        }
      } catch {
        /* 忽略 */
      }

      dragging = true;
      moved = false;
      lastAct = Date.now();
      startX = e.clientX;
      startY = e.clientY;
      startRight = parseInt(wrap.style.right || "22", 10);
      startBottom = parseInt(wrap.style.bottom || "22", 10);
      /* 冻结拖动起始时的盒子尺寸：拖动图比待机图宽很多，
         若实时读 offsetWidth，限制会随图片切换变化而顶住拖不动 */
      dragW = wrap.offsetWidth || 160;
      dragH = wrap.offsetHeight || 200;
      body.setPointerCapture?.(e.pointerId);
      if (holdTimer) clearTimeout(holdTimer);
      holdTimer = setTimeout(() => {
        holdTimer = null;
        if (!moved && !dragging) return;
        if (!moved) patHead();
      }, 700);
    });
    body.addEventListener("pointermove", (e: PointerEvent) => {
      if (!dragging) return;
      const dx = e.clientX - startX;
      const dy = e.clientY - startY;
      if (Math.abs(dx) + Math.abs(dy) > 4) {
        const firstMove = !moved;
        moved = true;
        if (holdTimer) {
          clearTimeout(holdTimer);
          holdTimer = null;
        }
        /* 首次移动立刻切拖拽姿势；之后限流刷新，避免每帧重排 */
        if (firstMove) {
          wrap.classList.add("wm-dragging-sway");
          sync();
        } else if (Date.now() - lastDragSync > 120) {
          lastDragSync = Date.now();
          sync();
        }
      }
      const w = dragW || 160;
      const h = dragH || 200;
      const maxRight = Math.max(4, window.innerWidth - w - 6);
      const maxBottom = Math.max(4, window.innerHeight - h - 6);
      wrap.style.right = Math.min(maxRight, Math.max(4, startRight - dx)) + "px";
      wrap.style.bottom = Math.min(maxBottom, Math.max(4, startBottom - dy)) + "px";
    });
    body.addEventListener("pointerup", () => {
      if (!dragging) return;
      dragging = false;
      wrap.classList.remove("wm-dragging-sway");
      setTimeout(() => sync(), 0);
      if (holdTimer) {
        clearTimeout(holdTimer);
        holdTimer = null;
      }
      lastAct = Date.now();
      if (moved) {
        try {
          const w2 = dragW || wrap.offsetWidth || 160;
          const h2 = dragH || wrap.offsetHeight || 200;
          let r2 = Math.min(Math.max(4, window.innerWidth - w2 - 6), Math.max(4, parseInt(wrap.style.right || "22", 10)));
          let b2 = Math.min(Math.max(4, window.innerHeight - h2 - 6), Math.max(4, parseInt(wrap.style.bottom || "22", 10)));

          /* 边缘吸附：靠近左右 + 底部时吸到角上，用缓动动画移动 */
          const SNAP = 72;
          const distLeft = window.innerWidth - r2 - w2;   /* 距左边缘 */
          const distRight = r2;                            /* 距右边缘 */
          if (distLeft < SNAP) r2 = window.innerWidth - w2 - 6;
          else if (distRight < SNAP) r2 = 6;
          if (b2 < SNAP) b2 = 6;

          /* 贴边收起：吸到左右边缘就缩进屏幕一半 */
          const edgeLeft = window.innerWidth - r2 - w2 <= 8;
          const edgeRight = r2 <= 8;
          wrap.classList.toggle("wm-edge-left", edgeLeft);
          wrap.classList.toggle("wm-edge-right", edgeRight);

          const willSnap =
            r2 !== parseInt(wrap.style.right || "22", 10) ||
            b2 !== parseInt(wrap.style.bottom || "22", 10);
          if (willSnap) {
            animateTo(r2, b2, 320);
          } else {
            wrap.style.right = r2 + "px";
            wrap.style.bottom = b2 + "px";
            localStorage.setItem(POS_KEY, JSON.stringify({ right: r2, bottom: b2 }));
          }
        } catch {
          /* 忽略 */
        }
        requestAnimationFrame(updateMirror);
    setTimeout(updateMirror, 300);
      }
    });
    window.addEventListener("resize", updateMirror);

    /* ---------- 状态机 tick ---------- */
    /* 每 5 秒检查一次：长任务计时、状态刷新 */
    setInterval(() => {
      try {
        if (busy) {
          if (thinkSince === 0) thinkSince = Date.now();
        } else {
          thinkSince = 0;
        }
        maybeQuietVolume();
        sync();
      } catch {
        /* 忽略 */
      }
    }, 5000);

    /* 待机随机小动作：空闲时约每 90 秒挑一个，持续 4 秒 */
    const IDLE_ACTIONS: State[] = ["stretch", "yawn", "scratch", "checkwatch"];
    /* 待机小动作 → 台词槽位（txt 里的 [皮肤.idle1] ~ [皮肤.idle4]） */
    const IDLE_SLOTS: Record<string, string> = {
      stretch: "idle1",
      yawn: "idle2",
      scratch: "idle3",
      checkwatch: "idle4",
    };
    setInterval(() => {
      try {
        if (busy || dragging || !bubble.hidden || hovering) return;
        if (state !== "idle") return;
        if (Date.now() < idleActUntil || Date.now() < greetUntil) return;
        if (Date.now() - lastAct < 20000) return;
        const h = new Date().getHours();
        /* 深夜更爱打哈欠 */
        const pool = h >= 22 || h < 6 ? (["yawn", "yawn", "stretch"] as State[]) : IDLE_ACTIONS;
        idleAct = pool[Math.floor(Math.random() * pool.length)];
        idleActUntil = Date.now() + 4000;
        sync();
        /* 小动作同时说一句（纯文字，不配音） */
        try {
          const slot = IDLE_SLOTS[idleAct] || "idle";
          const ln = pickLine(lastLine, resolveSkin(), slot);
          if (ln) {
            lastLine = ln;
            /* 第 4 参数 false：伴随式台词，不抢姿势（只见图 + 文字） */
            say(ln, 4000, false, false);
          }
        } catch {
          /* 忽略 */
        }
      } catch {
        /* 忽略 */
      }
    }, 90000);

    /* 定时问候：每天首次交互时，按时间段选早安 / 晚安 */
    function maybeGreet() {
      try {
        const now = new Date();
        const h = now.getHours();
        const dayKey =
          now.getFullYear() + "-" + String(now.getMonth() + 1).padStart(2, "0") + "-" +
          String(now.getDate()).padStart(2, "0");
        if (greetDay === dayKey) return;
        let kind: State | null = null;
        /* 调试开关：localStorage 里 wm-greet-debug = morning/noon/afternoon/evening/night */
        try {
          const dbg = (window.localStorage.getItem("wm-greet-debug") || "").trim();
          const map: Record<string, State> = {
            morning: "greet_morning",
            noon: "greet_noon",
            afternoon: "greet_afternoon",
            evening: "greet_evening",
            night: "greet_night",
          };
          if (map[dbg]) kind = map[dbg];
        } catch {
          /* 忽略 */
        }
        if (!kind) {
          if (h >= 8 && h < 11) kind = "greet_morning";
          else if (h >= 11 && h < 14) kind = "greet_noon";
          else if (h >= 14 && h < 18) kind = "greet_afternoon";
          else if (h >= 18 && h < 23) kind = "greet_evening";
          else if (h >= 23 || h < 2) kind = "greet_night";
        }
        if (!kind) return;
        greetDay = dayKey;
        greetKind = kind;
        greetUntil = Date.now() + 4500;
        sync();
        /* 问候语也走台词库：[皮肤.greet_morning] / [皮肤.greet_night] */
        try {
          const lnGreet = customFor(kind, resolveSkin());
          const fallback =
            kind === "greet_morning"
              ? "早上好。"
              : kind === "greet_noon"
                ? "中午了，吃饭了吗？"
                : kind === "greet_afternoon"
                  ? "下午好。"
                  : kind === "greet_evening"
                    ? "晚上好。"
                    : "夜深了，早点休息。";
          lastLine = lnGreet ? lnGreet.text : fallback;
          /* 问候配音：有音频就播（cus_ 文本指纹 / line_{皮肤}_greet_* 序号码），没有就纯文字 */
          if (lnGreet?.audio) speak(lnGreet.audio);
          say(lastLine, 6000, false);
        } catch {
          /* 忽略 */
        }
      } catch {
        /* 忽略 */
      }
    }
    setTimeout(maybeGreet, 1500);

    /* 双击 → 角色晃动（刷新余额已取消，双击专门留给晃动） */
    let feedbackTimer: any = null;
    body.addEventListener("dblclick", () => {
      if (feedbackTimer) {
        clearTimeout(feedbackTimer);
        feedbackTimer = null;
      }
      lastAct = Date.now();
      /* 抱头眩晕图 + 身体摇晃 + 语音「呃呃~」 */
      patUntil = 0;
      angryUntil = 0;
      shyUntil = 0;
      dizzyUntil = Date.now() + 2000;
      dizzy();
      playFx("dizzy_fx");
      const lnDiz = actionLine("dizzy");
      if (lnDiz) {
        speak(lnDiz.audio);
        say(lnDiz.text, 3500, false);
      } else {
        speak("dizzy");
      }
      sync();
      /* 眩晕结束自动复原 */
      setTimeout(() => sync(), 2500);
    });
    body.addEventListener(
      "click",
      (e) => {
        if (moved) {
          e.stopPropagation();
          moved = false;
        }
      },
      true,
    );

    /* ---------- 事件：任务开始 / 结束 ---------- */
    const offRunStart = feature.on("run_start", () => {
      busy = true;
      lastAct = Date.now();
      sync();
    });
    const offRunEnd = feature.on("run_end", (p: any) => {
      busy = false;
      playChime();
      speak("done");
      cheerUntil = Date.now() + 2000;
      setTimeout(() => sync(), 2200);
      acted = false;
      actions.style.display = "none";
      const dNum = Number(p && p.delta !== undefined ? p.delta : 0);
      if (Number.isFinite(dNum) && dNum > 0) sessionSpent += dNum;
      const d = p && p.delta !== undefined ? " · 本次 -" + p.delta : "";
      /* F6: 单次消耗偏高并入完成气泡（原来单独 say 会被下一句覆盖） */
      const spentNote =
        Number.isFinite(dNum) && dNum >= 1 ? "（这轮花得有点多：￥" + dNum.toFixed(2) + "）" : "";
      say(sysText("done", "✅ 任务完成啦") + d + spentNote, 8000);
      /* 任务完成：系统通知（需已授权） */
      /* 系统通知：已授权时额外弹一个 */
      try {
        if (typeof Notification === "undefined") {
          /* 环境不支持通知 */
        } else if (Notification.permission === "granted") {
          new Notification("螃蟹娘：任务完成", {
            body: p && p.delta !== undefined ? "本次消耗 ￥" + p.delta : "活干完啦，来看一眼余额吧",
          });
        } else if (Notification.permission === "denied" && !notifyDeniedHinted) {
          notifyDeniedHinted = true;
          say("浏览器把通知拦了…点地址栏左边的图标允许一下，下次就能弹啦", 12000);
        }
      } catch {
        /* 忽略 */
      }
      void refresh(false);
    });

    /* ---------- 启动 ---------- */
    void refresh(false);

    /* 轮询：失败指数退避（3min -> 6 -> 12 -> 24 -> 48 -> 60min 封顶） */
    let pollTimer: any = null;
    function nextDelay(): number {
      const base = 180_000;
      if (failCount <= 0) return base;
      return Math.min(60 * 60 * 1000, base * Math.pow(2, failCount));
    }
    function schedulePoll() {
      if (pollTimer) clearTimeout(pollTimer);
      pollTimer = setTimeout(async () => {
        if (cfg.quiet && inQuietHours()) {
          schedulePoll();
          return;
        }
        await refresh(false);
        schedulePoll();
      }, nextDelay());
    }
    schedulePoll();

    const stateTimer = setInterval(() => sync(), 30_000);

    setTimeout(() => {
      if (!bubble.hidden) return;
      acted = false;
      actions.style.display = "none";
      lastLine = pickLine(lastLine, resolveSkin());
      say(lastLine, 7000);
    }, 120_000);

    (window as any).__wmCrabChime = () => playChime();

    return () => {
      if (pollTimer) clearTimeout(pollTimer);
      clearInterval(stateTimer);
      if (hideTimer) clearTimeout(hideTimer);
      document.removeEventListener("keydown", onKey);
      offRunStart?.();
      offRunEnd?.();
      closeMenu();
      menu.remove();
      root.remove();
    };
  } catch {
    /* 角色挂载失败不影响插件其它功能 */
  }
}
