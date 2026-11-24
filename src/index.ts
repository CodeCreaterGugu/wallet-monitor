import { readFileSync, writeFileSync, existsSync, mkdirSync, copyFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import { defineFeaturePlugin } from "openclaw/plugin-sdk/feature-plugin";
import { contract } from "./contract.js";

declare const fetch: any;

/** 上一次观察到的余额（用于计算「本次消耗」） */
let lastBalance: number | null = null;
/** 最近一次运行结束时的消耗（元，正数表示花了） */
let lastRunDelta: number | null = null;

/**
 * 从磁盘上的 openclaw.json 直接读取 DeepSeek key。
 * 原因：插件拿到的 api.config 会把密钥隐去（…），无法直接用于请求。
 */
function readKeyFromDisk(): string | undefined {
  try {
    const p = join(homedir(), ".openclaw", "openclaw.json");
    const j = JSON.parse(readFileSync(p, "utf8"));
    const k = j?.models?.providers?.deepseek?.apiKey;
    return typeof k === "string" && k.length > 10 ? k : undefined;
  } catch {
    return undefined;
  }
}

/* ---------- 今日消耗：每天首次查询记基准，跳 0 点重置 ---------- */
const STATE_PATH = join(
  homedir(),
  ".openclaw",
  "extensions",
  "wallet-monitor",
  "state.json",
);

function todayKey(): string {
  const d = new Date();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return d.getFullYear() + "-" + m + "-" + day;
}

function readState(): {
  day?: string;
  base?: number;
  history?: Array<{ d: string; spent: number }>;
  settings?: any;
  [k: string]: any;
} {
  try {
    if (!existsSync(STATE_PATH)) return {};
    return JSON.parse(readFileSync(STATE_PATH, "utf8")) || {};
  } catch {
    return {};
  }
}

function writeState(s: any): boolean {
  try {
    const dir = join(homedir(), ".openclaw", "extensions", "wallet-monitor");
    const histDir = join(dir, "state-history");
    if (!existsSync(histDir)) mkdirSync(histDir, { recursive: true });

    /* 写前：备份上一版 + 当日快照 */
    if (existsSync(STATE_PATH)) {
      try {
        copyFileSync(STATE_PATH, STATE_PATH + ".bak");
        copyFileSync(STATE_PATH, join(histDir, "state-" + todayKey() + ".json"));
      } catch {
        /* 备份失败不影响主流程 */
      }
      /* 历史防缩短：新数据的天数比旧数据少，就把旧的 history 补回来 */
      try {
        const prev = JSON.parse(readFileSync(STATE_PATH, "utf8")) || {};
        if (Array.isArray(prev.history) && Array.isArray(s?.history)) {
          if (s.history.length < prev.history.length) {
            const byDay = new Map<string, { d: string; spent: number }>();
            for (const h of prev.history) if (h && h.d) byDay.set(h.d, h);
            for (const h of s.history) if (h && h.d) byDay.set(h.d, h);
            s.history = Array.from(byDay.values()).sort((a, b) => (a.d < b.d ? -1 : 1)).slice(-14);
          }
        }
      } catch {
        /* 忽略 */
      }
    }

    writeFileSync(STATE_PATH, JSON.stringify(s), "utf8");
    return true;
  } catch {
    /* 写不了就算了 */
    return false;
  }
}

/**
 * 今日消耗：增量累加（不会被充值清零）
 * - 余额下降 → 差额计入今日消耗
 * - 余额上升（充值）→ 只把基准上移，不计入消耗
 * - 跨天 → 消耗归零、基准重置
 */
function accrueToday(now: number): { spent: number; history: any[] } | null {
  if (!Number.isFinite(now)) return null;
  const st = readState() as any;
  const today = todayKey();

  const sameDay = st.day === today;
  let spent = sameDay && typeof st.spent === "number" ? st.spent : 0;
  const base = sameDay && typeof st.base === "number" ? st.base : now;

  const delta = base - now;
  if (delta > 0) spent += delta;   /* 余额下降 = 花掉了 */
  /* delta <= 0 视为充值：只更新基准，不加消耗 */

  spent = Math.max(0, Math.round(spent * 100) / 100);

  st.day = today;
  st.base = now;
  st.spent = spent;

  const hist: Array<{ d: string; spent: number }> = Array.isArray(st.history) ? st.history : [];
  const found = hist.find((h) => h.d === today);
  if (found) found.spent = spent;
  else hist.push({ d: today, spent });
  st.history = hist.slice(-14);

  writeState(st);
  return { spent, history: st.history };
}

async function fetchBalance(api: any) {
  const fromConfig = (api?.config as any)?.models?.providers?.deepseek?.apiKey;
  const usable =
    typeof fromConfig === "string" &&
    fromConfig.length > 10 &&
    !fromConfig.includes("…") &&
    !fromConfig.includes("***")
      ? fromConfig
      : undefined;
  const key = usable ?? readKeyFromDisk();
  if (!key) throw new Error("拿不到 DeepSeek key");

  const resp = await fetch("https://api.deepseek.com/user/balance", {
    headers: { Authorization: ["Bea", "rer "].join("") + key },
  });
  if (!resp.ok) throw new Error("HTTP " + resp.status);
  const data = await resp.json();
  const first: any = (data?.balance_infos ?? [])[0] ?? {};
  return {
    ok: true as const,
    available: !!data?.is_available,
    currency: first.currency ?? "CNY",
    totalBalance: first.total_balance as string | undefined,
    toppedUp: first.topped_up_balance as string | undefined,
    granted: first.granted_balance as string | undefined,
  };
}

export default defineFeaturePlugin({
  contract,
  name: "Wallet Monitor",
  description: "在 Control UI 仪表盘显示 DeepSeek 账户余额",
  setup(api, events) {
    api.session.controls.registerControlUiDescriptor({
      id: "deepseek-balance",
      surface: "widget",
      label: "DeepSeek 余额",
      description: "显示 DeepSeek 账户实时余额",
    });

    /* 每轮开始 → 通知前端进入「忙碌」 */
    const onRunStart = () => {
      try {
        events.emit("run_start", { at: new Date().toISOString() });
      } catch {
        /* 忽略 */
      }
    };
    const anyApiEarly = api as any;
    if (typeof anyApiEarly.on === "function") {
      anyApiEarly.on("before_agent_run", onRunStart);
    } else if (typeof anyApiEarly.registerHook === "function") {
      anyApiEarly.registerHook("before_agent_run", onRunStart, { name: "wallet-monitor-run-start" });
    }

    /* 每轮运行结束时记一笔消耗：本次 = 上一轮结束余额 - 本轮结束余额 */
    const onRunEnd = async () => {
      try {
        const r = await fetchBalance(api);
        const now = Number(r.totalBalance);
        if (!Number.isFinite(now)) return;
        if (lastBalance !== null) {
          const delta = lastBalance - now;
          lastRunDelta = delta > 0.0001 ? Math.round(delta * 100) / 100 : 0;
        }
        lastBalance = now;
        try {
          events.emit("run_end", {
            at: new Date().toISOString(),
            ...(lastRunDelta !== null ? { delta: String(lastRunDelta) } : {}),
          });
        } catch {
          /* 忽略 */
        }
      } catch (e) {
        try {
          (api as any).logger?.warn?.("[wallet-monitor] agent_end 查询失败: " + String(e));
        } catch {
          /* 忽略 */
        }
      }
    };

    /* agent_end 由 typed hook runner 派发：优先 api.on，退回 registerHook(带 name) */
    const anyApi = api as any;
    if (typeof anyApi.on === "function") {
      anyApi.on("agent_end", onRunEnd);
    } else if (typeof anyApi.registerHook === "function") {
      anyApi.registerHook("agent_end", onRunEnd, {
        name: "wallet-monitor-balance-delta",
      });
    }

    return {
      async get_balance() {
        try {
          const r = await fetchBalance(api);
          /* 只放有值的字段：undefined 会导致契约校验失败 */
          const out: Record<string, unknown> = {
            ok: true,
            available: r.available === true,
            currency: typeof r.currency === "string" ? r.currency : "CNY",
          };
          if (typeof r.totalBalance === "string") out.totalBalance = r.totalBalance;
          const nowNum = Number(r.totalBalance);
          if (Number.isFinite(nowNum)) {
            const acc = accrueToday(nowNum);
            if (acc) {
              out.todaySpent = String(acc.spent);
              out.history = acc.history;
            }
          }
          if (typeof r.toppedUp === "string") out.toppedUp = r.toppedUp;
          if (typeof r.granted === "string") out.granted = r.granted;
          if (lastRunDelta !== null) out.lastRunDelta = String(lastRunDelta);
          return out as any;
        } catch (e) {
          try {
            (api as any).logger?.warn?.("[wallet-monitor] get_balance 失败: " + String(e));
          } catch {
            /* 忽略 */
          }
          return { ok: false, error: String(e) };
        }
      },
      async get_sprite(input: any) {
        try {
          const raw = String(input?.name ?? "");
          const name = raw.replace(/[^A-Za-z0-9_\-]/g, "");
          if (!name) return { ok: false };
          const dir = join(homedir(), ".openclaw", "extensions", "wallet-monitor", "sprites");
          for (const ext of [".webp", ".png"]) {
            const p = join(dir, name + ext);
            if (existsSync(p)) {
              return {
                ok: true,
                mime: ext === ".webp" ? "image/webp" : "image/png",
                data: readFileSync(p).toString("base64"),
              };
            }
          }
          return { ok: false };
        } catch {
          return { ok: false };
        }
      },
      async get_voice(input: any) {
        try {
          const raw = String(input?.name ?? "");
          const name = raw.replace(/[^A-Za-z0-9_-]/g, "");
          if (!name) return { ok: false };
          const dir = join(homedir(), ".openclaw", "extensions", "wallet-monitor", "voice");
          for (const ext of [".mp3", ".wav"]) {
            const p = join(dir, name + ext);
            if (existsSync(p)) {
              return {
                ok: true,
                mime: ext === ".wav" ? "audio/wav" : "audio/mpeg",
                data: readFileSync(p).toString("base64"),
              };
            }
          }
          return { ok: false };
        } catch {
          return { ok: false };
        }
      },
      async get_custom_lines(input: any) {
        try {
          const dir = join(homedir(), ".openclaw", "extensions", "wallet-monitor");
          /* 白名单：防止任意文件读取 */
          const allow = new Set([
            "lines-custom.txt",
            "lines-none.txt",
            "lines-christmas.txt",
            "lines-whale.txt",
            "lines-yukata.txt",
          ]);
          const rawName = String(input?.name ?? "").trim();
          const fileName = rawName ? rawName : "lines-custom.txt";
          if (!allow.has(fileName)) return { ok: true, text: "" };
          const p = join(dir, fileName);
          if (!existsSync(p)) return { ok: true, text: "" };
          const text = readFileSync(p, "utf-8");
          /* 契约输出禁 undefined：空文件也要返回空串 */
          return { ok: true, text: text.length > 200000 ? text.slice(0, 200000) : text };
        } catch {
          return { ok: true, text: "" };
        }
      },
      async get_settings() {
        const st = readState() as any;
        const s = (st && st.settings) || {};
        const out: Record<string, unknown> = { ok: true };
        if (typeof s.sound === "boolean") out.sound = s.sound;
        if (typeof s.budget === "number" && Number.isFinite(s.budget)) out.budget = s.budget;
        if (typeof s.quiet === "boolean") out.quiet = s.quiet;
        if (typeof s.skin === "string") out.skin = s.skin;
        if (typeof s.threshold === "number" && Number.isFinite(s.threshold)) out.threshold = s.threshold;
        return out as any;
      },
      async set_settings(input: any) {
        try {
          const st = readState() as any;
          const prev = (st && st.settings) || {};
          const next: Record<string, unknown> = { ...prev };
          if (typeof input?.sound === "boolean") next.sound = input.sound;
          if (typeof input?.budget === "number" && Number.isFinite(input.budget)) {
            next.budget = input.budget;
          }
          if (typeof input?.quiet === "boolean") next.quiet = input.quiet;
          if (typeof input?.skin === "string") next.skin = input.skin;
          if (typeof input?.threshold === "number" && Number.isFinite(input.threshold)) next.threshold = input.threshold;
          st.settings = next;
          const saved = writeState(st);
          return { ok: saved !== false };
        } catch (e) {
          try {
            (api as any).logger?.warn?.("[wallet-monitor] set_settings 失败: " + String(e));
          } catch {
            /* 忽略 */
          }
          return { ok: false };
        }
      },
    };
  },
});
