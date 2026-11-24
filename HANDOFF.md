# 交接文档 · wallet-monitor（余额监控 + 螃蟹娘桌宠）

> 更新时间：2026-11-01
> 用途：新会话接手时的唯一入口文档。先读这份，再动代码。

---

## 一、这是什么

一个 **OpenClaw Control UI 插件**，把「DeepSeek 余额监控」做成了桌面宠物（螃蟹娘）形态：

- 会话头部胶囊：余额 + 状态点
- 屏幕右下角悬浮角色：会走动、会说话、会换装、会随任务状态变化
- 点击角色不同部位触发不同互动（含语音）

---

## 二、关键路径

| 用途 | 路径 |
|---|---|
| **插件源码** | `C:\Users\21674\.openclaw\extensions\wallet-monitor` |
| 立绘素材（懒加载） | `...\wallet-monitor\sprites\*.webp`（25 张） |
| 语音素材（懒加载） | `...\wallet-monitor\voice\*.mp3/wav`（33 段） |
| 状态与设置 | `...\wallet-monitor\state.json` |
| 状态备份/快照 | `state.json.bak`、`state-history\state-YYYY-MM-DD.json` |
| 一键构建 | `...\wallet-monitor\build.bat` |
| 素材清单生成 | `...\wallet-monitor\scripts\gen-manifests.mjs` |
| 文档 | `ROADMAP.md`、`POSE-PLAN.md`、`POSES-MATRIX.md`、`HANDOFF.md`（本文件） |
| 生图参考图 | `C:\Users\21674\.openclaw\media\crab-refs\` |
| 生图代理 | `D:\AI生成\图片生成代理\proxy.py`（端口 8787，`strength.txt` 控保真度） |
| 点阵素材原图 | `D:\AI生成\图片\螃蟹娘\动作\{base,web,原图_已通过,原图_未通过}` |
| 预览图交付 | `D:\AI生成\看图\`（桌面有快捷方式 `看图.lnk`） |

---

## 三、架构

```
Control UI (浏览器)
├── src/control-ui.ts      入口：activate() 里创建 feature client → mountCrab(feature)
├── src/crab.ts            桌宠主体（状态机、交互、气泡、设置面板、动画）
├── src/crab-icon.ts       气泡按钮图标（base64，内嵌）
├── src/crab-idle.ts       首帧 idle（内嵌，保证秒开）
├── src/crab-images.ts     【自动生成】立绘名字清单
├── src/crab-voice.ts      【自动生成】语音名字清单
└── src/control-ui.css     全部样式

Gateway 后端（Node）
├── src/index.ts           get_balance / get_settings / set_settings / get_voice / get_sprite
├── src/contract.ts        契约（操作名、事件名、输入输出 schema）
└── state.json             今日基准、累计消耗、历史、设置
```

### 懒加载机制（重要）

- 立绘/语音**不进 bundle**，按需通过 `get_sprite` / `get_voice` 请求后端读取文件
- 名字清单由 `scripts/gen-manifests.mjs` 在 `prebuild` 阶段**扫描目录自动生成**
- 只有 `idle` 一张内嵌（`crab-idle.ts`），保证首屏立即有图
- 缓存：前端 `spriteCache` / `voiceCache`（Map），竞态用序号守卫

**以后加素材只需**：

```
① 图片丢进 sprites\<key>.webp
② 语音丢进 voice\<key>.mp3
③ 构建（清单自动更新）
④ 代码里引用 key
```

---

## 四、构建与部署（必须遵守）

```bat
cd C:\Users\21674\.openclaw\extensions\wallet-monitor
build.bat
```

`build.bat` 四步：`npm install` → 重建 `node_modules\openclaw` Junction → `npm run build` → 清 node_modules 只留生产依赖。

**部署**：改完必须 `/restart` 网关才生效（Windows 下 plugin reload 走不通，符号链接 EPERM）。

**顺序**：先构建完成，再 `/restart`，否则会报
`Plugin source changed while preparing its reload`（重查一次即可恢复）。

---

## 五、当前功能（已完成）

### 余额
查询、头部胶囊、状态点（红≤阈值/黄≤2倍/绿）、点击刷新、悬停明细、本次消耗、今日消耗（**增量累加，充值不清零**）、7 天趋势、14 天热力图、周对比（近 7 天 vs 前 7 天）、可用天数预测、预算、可配阈值、峰谷判断（含**中国法定节假日表 2026**）、数据新鲜度、低余额通知、指数退避刷新、三层数据保护（写前备份/每日快照/历史防缩短）。

### 桌宠
20 个动作：idle / talk / busy / cheer / wave / settle / sleep / low / error / full / think / shy / drag / stretch / yawn / scratch / checkwatch / greet_morning / greet_night / pat_happy / angry / dizzy。

状态优先级：`full > dizzy > drag > pat_happy > angry > shy > cheer > think > busy > 气泡(low/talk) > greet > 待机小动作 > wave > sleep > settle > idle`。

交互：
- 点**头** → 高兴（pat_happy）+「好舒服～」
- 点**身子** → 生气 + **180° 转身**（`wm-turn`）
- 点**腿** → 害羞 +「嗯……」
- **双击** → 眩晕（`dizzy`）+ 摇摆 ±4.5°；**眩晕中再点** → 重置 2 秒计时 + 重播摇摆 + 一句台词
- 长按 700ms → 摸头
- 拖拽 → 被鼠标拎起（`drag`），过屏幕中线 **3D 翻面**
- 靠近左右边缘 → **吸附 + 收起 30%**，悬停展开（离开 0.3 秒才缩回），收起时隐藏余额按钮
- 空闲 3 分钟 → settle，30 分钟 → sleep，空闲随机小动作（stretch/yawn/scratch/checkwatch）

### 皮肤
三套：基础（128×375）、圣诞（113×375，白长筒袜）、鲸鱼（172×375，蓝白条纹袜+小白鞋）。
设置面板里有**缩略图选择**；换装动画 = 新图从上方滑入（旧图垫底）。

### 语音
33 段，全部懒加载。互动台词（pat/angry/shy/dizzy/legs 各 3~4 句）来自 MiniMax T2A。
音量滑条（0~100，0 时静音）、音效开关、深夜静音（23:00-06:00 自动降音量一次）。

### 设置面板
右键 →「⚙️ 设置」→ 面板：全部静音（已移除）/ 音效 / 深夜静音 / 装扮缩略图 / 告急阈值 / 今日预算 / 音量 / 透明度 / **恢复默认** / **保存** / 版本 1.0.0。

专注模式：拖透明度条、或悬停装扮区 **0.75 秒/点击** → 其余内容与面板底渐隐。

### 其它
- 任务完成：浏览器系统通知（权限在 pointerdown 申请）
- 成本异常提醒：单次 ≥ 1 元时提示
- 余额面板：白底橙描边 + 大字「余额 ￥x.xx」+ 黑色小字数据 + 热力图（仅详情）

---

## 六、踩过的坑（务必知道）

| # | 坑 | 现象 | 解法 |
|---|---|---|---|
| 1 | **typebox 版本** | 插件加载失败 `ERR_MODULE_NOT_FOUND ... typebox/build/index.mjs` | `package.json` 锁定 `typebox: "1.3.17"`（1.4.3 没有该入口） |
| 2 | **mountCrab 需要 feature client** | 语音/设置全部失效，或整个角色不挂载 | `control-ui.ts` 里 `createFeatureClient(contract, host)` 后传入 |
| 3 | **契约 ID 规则** | 操作名/事件名报错 | 只能小写 + `_`/`.`/`-`，不能驼峰 |
| 4 | **契约输出禁 undefined** | `FEATURE OUTPUT MUST BE FOUNDED JSON` | 只放有值的字段 |
| 5 | **Bearer 字面量** | 写进文件变 `***` | 用 `"Bea" + "rer "` 拼接 |
| 6 | **WAAPI `fill: "both"`** | 翻转/转身失效（transform 被锁） | 改 `fill: "none"`，需要时 `imgAnim.cancel()` |
| 7 | **`updateMirror` 取消动画** | 换装滑动动画刚播就被掐 | 已移除该 cancel |
| 8 | **懒加载首帧** | 只看到按钮 / 破图 | `img.src = CRAB_IDLE` 同步赋值 |
| 9 | **换电/清空 state** | 今日消耗变 0 | 已改为增量累加；state 有备份与快照 |
| 10 | **换日后整体覆盖** | 历史与设置被清空 | `accrueToday` 合并写入，不整体覆盖 |
| 11 | **立绘宽度差异** | 切换时角色横向跳 | 新图尽量与原图同宽（圣诞 113、鲸鱼 172、基础 128） |
| 12 | **`.bat`/`.ps1` 中文** | 乱码/静默退出 | 内容全 ASCII 或存 UTF-8 BOM |
| 13 | **GBK 源码** | edit 工具拒绝 | 用 `[IO.File]::ReadAllText($p, [Text.Encoding]::GetEncoding(936))` 字节级改写 |

---

## 七、素材生产流程

### 立绘（图生图）

```
参考图放 C:\Users\21674\.openclaw\media\crab-refs\（必须是允许目录）
image_generate：images=[姿势参考, 服装参考] + 详细 prompt
strength：0.42~0.55（改小更贴原图，改大更自由）
```

### 后处理（Python + PIL）

```
① floodfill 从四角去白底 + BFS 清边缘
② 封闭白洞清理（面积 40~1500px，避免误删白色衣物）
③ 稳健边界裁剪（忽略 <3 不透明像素的列/行，防零星杂点撑宽）
④ 缩放到高度 375 → WebP quality 84 → 存 sprites\<key>.webp
```

### 语音

MiniMax `speech-02-hd`，`voice_id = female-shaonv`，输出 mp3 → `voice\<key>.mp3`。

### 生图代理（重要，独立组件）

**位置**：`D:\AI生成\图片生成代理\proxy.py`
**端口**：`127.0.0.1:8787`
**日志**：同目录 `proxy.log`

#### 它解决什么问题

OpenClaw 的 `image_generate` 走 OpenAI 风格接口，而火山方舟 seedream 有两处不兼容：

| 问题 | 代理的处理 |
|---|---|
| 方舟**没有** `/images/edits` 端点（图生图也走 generations） | 一律转发到 `/images/generations`，参考图放 `image` 字段 |
| 客户端用 `multipart/form-data` 上传，代理早期只认 JSON → 解析失败提前回包 → 连接被重置（`UND_ERR_SOCKET`） | 代理 v2 支持 multipart：解析出 image 文件转 data URI |
| 客户端可能用 chunked 传输 | v2 支持逐块读取 |

#### strength（保真度）

同目录 `strength.txt`，写一个 0~1 的数字，**请求时实时读取，改完不用重启**：

| 值 | 效果 |
|---|---|
| 0.2~0.3 | 极贴近原图，只轻微改画风 |
| 0.42 | 保角色一致，允许换姿态（**常用**） |
| 0.5~0.55 | 套换服装（三视图 → 立绘） |
| 0.7+ | 自由发挥，构图容易跑偏 |

#### 启停

```powershell
# 状态
Get-NetTCPConnection -LocalPort 8787 -State Listen
curl.exe -s http://127.0.0.1:8787/health

# 重启（先杀旧进程）
Get-NetTCPConnection -LocalPort 8787 -State Listen | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
Start-Sleep -Seconds 2
Start-Process -FilePath 'pythonw.exe' -ArgumentList 'proxy.py' -WorkingDirectory 'D:\AI生成\图片生成代理' -WindowStyle Hidden
Start-Sleep -Seconds 4
```

#### 常见故障

| 现象 | 原因 | 处理 |
|---|---|---|
| `fetch failed / other side closed` | 代理没跑，或跑的是旧版本 | 按上面命令重启 |
| 图生图无变化、跟原图一样 | `strength` 太低 | 调到 0.5+ |
| 多图只生效一张 | 旧版代理把同名 `image[]` 覆盖成一个 | v2 已修，确认是 v2 |
| 401 / 400 | key 不对或端点错 | 用 `/api/v3`，不要 `/api/coding/v3` |

> 代理代码改动后必须重启进程（Python 不热重载）。

---

## 八、待办（详见 ROADMAP.md）

| 优先 | 事项 |
|---|---|
| 大 | **圣诞 / 鲸鱼 各补 19 个动作**（现各只有 idle，共约 38 张图） |
| 中 | 打包成可安装插件 |
| 中 | 多 key 汇总（DeepSeek/MiniMax/方舟） |
| 中 | 自定义皮肤包 |
| 小 | 设置重置（已做）/ 导出 CSV / 减少动效模式 |
| 受限 | 会话用量统计（插件 SDK 无 token 接口，需 Gateway 侧支持） |

---

## 九、常用命令

```powershell
# 构建
cd C:\Users\21674\.openclaw\extensions\wallet-monitor
cmd /c build.bat

# 查插件是否加载正常（角色消失时第一时间跑这个）
openclaw plugins doctor

# 系统诊断
openclaw doctor --non-interactive

# 看当前状态
Get-Content state.json -Raw

# 生图代理状态
Get-NetTCPConnection -LocalPort 8787 -State Listen
curl.exe -s http://127.0.0.1:8787/health
```

---

## 十、给新会话的提醒

1. **改完必须构建 + `/restart`**，否则看不到效果
2. **构建和重启不要同时进行**（会报 source changed，重查一次即可）
3. 用户要求：**生成预览图放 `D:\AI生成\看图\`**（桌面有快捷方式），聊天里也附一份
4. 用户发 **`1`** 表示「我在看上一张图」，**不是通过**
5. 改素材画幅前先问，用户明确说过不要动他的画幅
6. 每加一张图/一段语音，**不需要改代码**，丢进目录构建即可
7. 角色消失先跑 `openclaw plugins doctor`，九成是加载错误
