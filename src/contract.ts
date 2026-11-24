import { Type } from "typebox";
import { defineFeatureContract } from "openclaw/plugin-sdk/feature-contract";

export const contract = defineFeatureContract({
  pluginId: "wallet-monitor",
  operations: {
    get_balance: {
      kind: "query",
      description: "查询 DeepSeek 账户余额",
      input: Type.Object({}, { additionalProperties: false }),
      output: Type.Object({
        ok: Type.Boolean(),
        available: Type.Optional(Type.Boolean()),
        currency: Type.Optional(Type.String()),
        totalBalance: Type.Optional(Type.String()),
        toppedUp: Type.Optional(Type.String()),
        granted: Type.Optional(Type.String()),
        lastRunDelta: Type.Optional(Type.String()),
        todaySpent: Type.Optional(Type.String()),
        history: Type.Optional(
          Type.Array(
            Type.Object({
              d: Type.String(),
              spent: Type.Number(),
            }),
          ),
        ),
        error: Type.Optional(Type.String()),
      }),
    },
    get_sprite: {
      kind: "query",
      description: "按需读取立绘（懒加载）",
      input: Type.Object({ name: Type.String() }, { additionalProperties: false }),
      output: Type.Object({
        ok: Type.Boolean(),
        mime: Type.Optional(Type.String()),
        data: Type.Optional(Type.String()),
      }),
    },
    get_voice: {
      kind: "query",
      description: "按需读取语音文件（base64，懒加载）",
      input: Type.Object({ name: Type.String() }, { additionalProperties: false }),
      output: Type.Object({
        ok: Type.Boolean(),
        mime: Type.Optional(Type.String()),
        data: Type.Optional(Type.String()),
      }),
    },
    get_custom_lines: {
      kind: "query",
      description: "读取自定义台词文件（纯文本，前端解析）：不传 name 读 lines-custom.txt",
      input: Type.Object(
        { name: Type.Optional(Type.String()) },
        { additionalProperties: false },
      ),
      output: Type.Object({
        ok: Type.Boolean(),
        text: Type.Optional(Type.String()),
      }),
    },
    get_settings: {
      kind: "query",
      description: "读取桌宠设置（后端持久化，跨设备/清缓存不丢）",
      input: Type.Object({}, { additionalProperties: false }),
      output: Type.Object({
        ok: Type.Boolean(),
        sound: Type.Optional(Type.Boolean()),
        budget: Type.Optional(Type.Number()),
        quiet: Type.Optional(Type.Boolean()),
        skin: Type.Optional(Type.String()),
        threshold: Type.Optional(Type.Number()),
      }),
    },
    set_settings: {
      kind: "action",
      description: "保存桌宠设置到后端 state.json",
      input: Type.Object(
        {
          sound: Type.Optional(Type.Boolean()),
          budget: Type.Optional(Type.Number()),
          quiet: Type.Optional(Type.Boolean()),
          skin: Type.Optional(Type.String()),
          threshold: Type.Optional(Type.Number()),
        },
        { additionalProperties: false },
      ),
      output: Type.Object({ ok: Type.Boolean() }),
    },
  },
  events: {
    run_start: Type.Object({ at: Type.String() }),
    run_end: Type.Object({
      at: Type.String(),
      delta: Type.Optional(Type.String()),
    }),
  },
});
