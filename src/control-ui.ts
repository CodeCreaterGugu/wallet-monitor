import { defineControlUiPlugin } from "openclaw/plugin-sdk/control-ui";
import { createFeatureClient } from "openclaw/plugin-sdk/feature-contract";
import { contract } from "./contract.js";
import { mountCrab } from "./crab.js";
import "./control-ui.css";

const REFRESH_MS = 180_000; // 3 分钟

export default defineControlUiPlugin({
  id: contract.pluginId,
  activate(host) {
    /* 螃蟹娘悬浮角色（可拖拽 + 气泡 + 操作） */
    /* 关键：mountCrab 需要 feature client 才能 invoke 后端操作（语音/设置） */
    let feature: any = host as any;
    try {
      feature = createFeatureClient(contract, host as any);
    } catch {
      feature = host as any;
    }
    mountCrab(feature);

    /* ---------- 仪表盘组件（可选，用户可自行添加到面板） ---------- */
    host.ui.registerWidget({
      id: "deepseek-balance",
      label: "DeepSeek 余额",
      mount(container, context) {
        const feature = createFeatureClient(contract, context.host);

        const root = document.createElement("section");
        root.className = "wm-card";

        const title = document.createElement("div");
        title.className = "wm-title";
        title.textContent = "💰 DeepSeek 余额";

        const body = document.createElement("div");
        body.className = "wm-body";
        body.textContent = "查询中…";

        const meta = document.createElement("div");
        meta.className = "wm-meta";
        meta.textContent = "";

        const btn = document.createElement("button");
        btn.className = "wm-btn";
        btn.textContent = "刷新";
        btn.onclick = () => void refresh();

        root.append(title, body, meta, btn);
        container.append(root);

        let disposed = false;

        async function refresh() {
          if (disposed || context.signal.aborted) return;
          try {
            const r = await feature.invoke("get_balance", {});
            if (disposed || context.signal.aborted) return;
            if (!r.ok) {
              body.textContent = "查询失败：" + (r.error ?? "未知错误");
              body.className = "wm-body wm-error";
              meta.textContent = "";
            } else {
              const total = Number(r.totalBalance ?? "0");
              let cls = "wm-body";
              if (total <= 10) cls += " wm-critical";
              else if (total <= 20) cls += " wm-warn";
              body.className = cls;
              body.textContent =
                "¥" + (r.totalBalance ?? "—") +
                (r.available ? "  ✅ 可用" : "  ⚠️ 不可用");
              const d = r.lastRunDelta;
              meta.textContent =
                "充值 " + (r.toppedUp ?? "—") +
                " · 赠金 " + (r.granted ?? "—") +
                " · 本次 " + (d === undefined ? "—" : "-" + d);
            }
          } catch (e) {
            if (!disposed && !context.signal.aborted) {
              body.textContent = "查询异常：" + String(e);
              body.className = "wm-body wm-error";
            }
          }
        }

        void refresh();
        const timer = setInterval(() => void refresh(), REFRESH_MS);

        return {
          dispose: () => {
            disposed = true;
            clearInterval(timer);
            root.remove();
          },
        };
      },
    });

    /* ---------- 会话头部胶囊：两个可点区域 ---------- */
    host.ui.registerAccessory({
      id: "deepseek-balance-chip",
      placement: "session-header",
      mount(container, context) {
        const feature = createFeatureClient(contract, context.host);

        const root = document.createElement("span");
        root.className = "wm-chip";

        const main = document.createElement("button");
        main.type = "button";
        main.className = "wm-chip-seg wm-chip-main";

        const brand = document.createElement("span");
        brand.className = "wm-brand";
        brand.textContent = "Deepseek";

        const dot = document.createElement("span");
        dot.className = "wm-dot";
        dot.textContent = "●";

        const amount = document.createElement("span");
        amount.className = "wm-amount";
        amount.textContent = "…";

        main.append(brand, dot, amount);

        const sep = document.createElement("span");
        sep.className = "wm-sep";
        sep.textContent = "·";

        const alt = document.createElement("button");
        alt.type = "button";
        alt.className = "wm-chip-seg wm-chip-alt";
        alt.textContent = "本次 —";

        root.append(main, sep, alt);

        let disposed = false;
        let mode = 0; // 0=本次 1=今日 2=充值 3=赠金
        let data: any = null;

        function render() {
          if (!data) return;
          if (!data.ok) {
            amount.textContent = "失败";
            dot.dataset.level = "critical";
            alt.textContent = "点此重试";
            root.title = "DeepSeek 查询失败：" + (data.error ?? "未知错误");
            return;
          }
          const total = Number(data.totalBalance ?? "0");
          amount.textContent = "¥" + (data.totalBalance ?? "—");
          dot.dataset.level = total <= 10 ? "critical" : total <= 20 ? "warn" : "ok";

          const d = data.lastRunDelta;
          if (mode === 0) alt.textContent = d === undefined ? "本次 —" : "本次 -" + d;
          else if (mode === 1)
            alt.textContent =
              data.todaySpent === undefined ? "今日 —" : "今日 -" + data.todaySpent;
          else if (mode === 2) alt.textContent = "充值 ¥" + (data.toppedUp ?? "—");
          else alt.textContent = "赠金 ¥" + (data.granted ?? "—");

          root.title =
            "DeepSeek 余额 ¥" + (data.totalBalance ?? "—") +
            "\n充值 " + (data.toppedUp ?? "—") +
            " · 赠金 " + (data.granted ?? "—") +
            "\n本次消耗 " + (d === undefined ? "—" : "-" + d) +
            "\n今日消耗 " + (data.todaySpent === undefined ? "—" : "-" + data.todaySpent) +
            "\n（点金额刷新 / 点右侧切换视图）";
        }

        async function refresh() {
          if (disposed || context.signal.aborted) return;
          try {
            const r = await feature.invoke("get_balance", {});
            if (disposed || context.signal.aborted) return;
            data = r;
          } catch (e) {
            if (disposed || context.signal.aborted) return;
            data = { ok: false, error: String(e) };
          }
          render();
        }

        main.onclick = () => void refresh();
        alt.onclick = () => {
          mode = (mode + 1) % 4;
          render();
        };

        container.append(root);
        void refresh();
        const timer = setInterval(() => void refresh(), REFRESH_MS);

        return {
          dispose: () => {
            disposed = true;
            clearInterval(timer);
            root.remove();
          },
        };
      },
    });
  },
});
