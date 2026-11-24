# wallet-monitor 功能清单 + 姿势矩阵规划

> 更新时间：2026-10-30
> 用途：先定清单，再批量生成，避免边做边改

---

## 一、功能清单

### 已完成

| 分类 | 功能 |
|---|---|
| 余额 | 查询、头部胶囊、状态点（红≤¥10/黄/绿）、点击刷新、悬停明细 |
| 余额 | 本次消耗、今日消耗（跨 0 点重置）、7 天趋势、充值/赠金/预算、峰谷判断、新鲜度 |
| 余额 | 低余额浏览器通知、指数退避刷新 |
| 桌宠 | 13 张立绘、状态优先级、`run_start`/`run_end` 事件驱动 |
| 桌宠 | 拖拽限位 + 位置记忆、左右镜像、Ctrl+Shift+U 显隐、🦀 角标 |
| 桌宠 | 深夜静音、节日自动换装、呼吸起伏（纯 CSS 2.2%） |
| 交互 | 单击气泡反馈、双击晃动（轴心脚底 ±2.5°）、长按摸头、右键菜单 |
| 语音 | 9 段语音、单例播放、音效开关 |
| 设置 | 5 个独立 localStorage 键 + **后端 state.json 持久化**（get/set_settings） |
| 设置 | 面板内输入框设预算（已弃用 window.prompt） |
| 气泡按钮 | 橙描边白填充大中小三椭球、左脸侧位、镜像、面板打开时隐藏 |
| 基建 | 本地图生图代理 v2（multipart/chunked/多图数组/strength 注入/详细日志） |

### 待做

| 优先级 | 功能 | 工作量 |
|---|---|---|
| P0 | 皮肤 × 动作矩阵（3 套 × 12 动作） | 大 |
| P1 | 自定义余额阈值（界面上直接改） | 小 |
| P1 | 台词库扩充（每动作 3~5 句随机） | 小 |
| P1 | 余额告急语音提醒 | 小 |
| P1 | 中国法定节假日表（修峰谷误报） | 小 |
| P2 | 会话用量统计（需验 RPC 权限） | 中 |
| P2 | 预测可用天数、每日/每周报告、CSV 导出 | 小 |
| P2 | 待机小动作、走到目标位置、贴边收起、透明度 | 中 |
| P2 | 音色改「调皮+慵懒」、余额播报 | 小 |
| P3 | 配置面板化（开关/滑块）、皮肤预览缩略图、自定义皮肤包 | 中 |
| P3 | 打包成可安装插件、立绘懒加载 | 中 |

---

## 二、动作（姿势）总表

共 **12 个动作**，这是要固定的"标准姿势集"。

| # | ID | 中文名 | 触发场景 | 姿态要点 | 表情 | 优先级 |
|---|---|---|---|---|---|---|
| 1 | `idle` | 待机 | 默认状态 | 站立，重心一条腿，手臂自然垂 | 平静微笑 | **P0** |
| 2 | `talk` | 说话 | 气泡显示 / 对话中 | 半侧身，一手轻抬作说话状 | 张嘴说话 | **P0** |
| 3 | `busy` | 忙碌 | `run_start` | 坐地抱键盘敲击，前倾 | 专注皱眉 | **P0** |
| 4 | `cheer` | 欢呼 | `run_end` 完成 | 跳起，双手上举 | 眯眼大笑 | **P0** |
| 5 | `wave` | 打招呼 | 鼠标悬停 | 单手高举挥动，另一手叉腰 | 露齿笑 | P1 |
| 6 | `settle` | 歇会儿 | 静止 3 分钟后 | 坐在书堆上，双腿并拢 | 放松半闭眼 | P1 |
| 7 | `sleep` | 睡觉 | 静止 30 分钟 | 蜷缩侧躺，手垫脸下 | 闭眼 + 鼾泡 | P1 |
| 8 | `low` | 没精神 | 余额低于阈值 | 蹲坐抱膝 / 双手捧空碗 | 委屈下垂眼 | P1 |
| 9 | `error` | 出错 | 查询失败、任务失败 | 歪头抱头，一只手挠头发 | 困惑流汗 | P1 |
| 10 | `full` | 满足 | 充值后 12 秒 | 站立，手轻搭腰侧 | 满足眯眼 | P2 |
| 11 | `pat` | 被摸头 | 长按 700ms | 微微低头蹭，双手举起 | 开心闭眼 | P2 |
| 12 | `think` | 思考 | 长任务运行中 | 单手托腮，眼往上看 | 若有所思 | P2 |

### 基础装扮已有情况

| 已有 | 缺 |
|---|---|
| idle, talk, busy, cheer, wave, settle, sleep, low, error, full（10 个） | `pat`、`think` |

---

## 三、皮肤 × 动作 矩阵

### 皮肤清单（新年装已停用）

| ID | 名称 | 三视图 |
|---|---|---|
| `base` | 基础装扮（黑色连衣裙 + 深蓝狗爪领带 + 绿色 0/1 代码） | ✅ `turnaround-template-v8.png` |
| `christmas` | 圣诞装（红白 + 长筒白袜） | ✅ 已生成 |
| `whale` | 鲸鱼连帽衫 | ✅ 正在重做帽子版 |

### 矩阵规模

| 批次 | 范围 | 张数 |
|---|---|---|
| 第 1 批（P0） | 3 皮肤 × 4 动作（idle/talk/busy/cheer） | **12** |
| 第 2 批（P1） | 3 皮肤 × 5 动作（wave/settle/sleep/low/error） | **15** |
| 第 3 批（P2） | 3 皮肤 × 3 动作（full/pat/think） | **9** |
| 合计 | | **36 张** |

> 若后续想要更多皮肤，每加一套 = 多 12 张。

---

## 四、文件与命名规范

### 立绘源文件（大图，PNG）

```
D:\AI生成\图片\螃蟹娘\动作\{skin}\{action}.png
  例：D:\AI生成\图片\螃蟹娘\动作\christmas\idle.png
```

### 打包进插件的压缩图（WebP，宽 ≤ 380px）

```
D:\AI生成\图片\螃蟹娘\动作\web\{skin}_{action}.webp
  例：web\christmas_idle.webp
```

### 代码里的键名

```ts
// crab-images.ts
export const CRAB_IMAGES: Record<string, string> = {
  base_idle: "data:image/webp;base64,...",
  christmas_idle: "data:image/webp;base64,...",
  ...
};
```

> 兼容策略：旧键 `idle`、`christmas` 等保留，新皮肤动作按 `<skin>_<action>` 查表，找不到就回退到同动作的 `base_*`。

---

## 五、生成顺序

```
① 皮肤三视图定稿（base / christmas / whale）
② 第 1 批 P0：12 张
③ 第 2 批 P1：15 张
④ 第 3 批 P2：9 张
```

每批出图后 → 抠透明底 → 压缩 WebP → 入库 → 构建。

---

## 六、提示词骨架

### 动作图（以对应皮肤三视图为参考）

```
Character illustration of the crab girl in [皮肤名] outfit,
[动作姿态描述：体态/手部/腿部/视线],
[表情描述],
single character, full body, centered,
flat pure white background, no text, no props other than [必要道具],
clean anime line art, flat cel shading,
consistent with the reference turnaround sheet
```

参考图：该皮肤的 `turnaround-<skin>.png`（1 张）
`strength`：0.42（保留角色一致性，允许姿态变化）

### 三视图

```
Character turnaround sheet: three full-body views side by side
(FRONT, SIDE, BACK), same scale, aligned heights, feet on one ground line,
plain white background, reference-sheet quality, no text
+ 服装与角色取自第二张参考图
```

参考图：`turnaround-template-v8.png` + `outfit-<skin>.png`（2 张）
`strength`：0.5（套服装）／0.42（改姿态）

---

## 七、待确认项

- [ ] 12 个动作的定义是否 OK，要不要增删
- [ ] P0/P1/P2 分层是否接受
- [ ] 是否 3 套皮肤都要全 12 动作（36 张），还是先做 P0（12 张）
