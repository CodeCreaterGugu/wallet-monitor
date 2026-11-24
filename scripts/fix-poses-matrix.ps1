$ErrorActionPreference = "Stop"
$p = "C:\Users\21674\.openclaw\extensions\wallet-monitor\POSES-MATRIX.md"
$u8 = New-Object System.Text.UTF8Encoding($false)
$t = [IO.File]::ReadAllText($p, $u8)

# 1) 版本行
$old = "> 固化版本：v2 · 2026-10-30"
$new = "> 固化版本：v3 · 2026-11-01（A 列已按 sprites/ 实测核对）"
if (-not $t.Contains($old)) { throw "header not found" }
$t = $t.Replace($old, $new)

# 2) 逐行替换 **缺图** -> 现有，跳过 walk 行（14 号）
$nl = if ($t.Contains("`r`n")) { "`r`n" } else { "`n" }
$lines = $t -split [regex]::Escape($nl)
$done = 0
for ($i = 0; $i -lt $lines.Count; $i++) {
    $ln = $lines[$i]
    if ($ln -like "| 14 |*") { continue }
    if ($ln.Contains("**缺图**")) {
        $lines[$i] = $ln.Replace("**缺图**", "现有")
        $done++
    }
}
if ($done -lt 1) { throw "no rows replaced" }
$t = ($lines -join $nl)

# 3) 追加计划外动作小节
$append = @"

---

## 七、计划外动作（2026-11-01 补记）

基础套装除上表 20 个动作外，代码里还实装了 3 个动作（不在原计划矩阵内）：

| 动作 key | 名称 | 触发 | A 基础 | B 圣诞 | C 鲸鱼 |
|---|---|---|---|---|---|
| ``angry`` | 生气 + 180° 转身 | 点身子 | 现有 | | |
| ``dizzy`` | 眩晕摇摆 | 双击 / 眩晕中再点 | 现有 | | |
| ``drag`` | 被鼠标拎起 | 拖拽中 | 现有 | | |

> ``walk`` 仍缺图：走路动画（B12）未做，拖拽位移暂由 ``drag`` 承担。
> B / C 列留空，按上文规则（空着 = 按默认姿态生成）。
"@
$append = $append -replace "`r`n", $nl
if (-not $t.Contains("计划外动作")) {
    $t = $t.TrimEnd() + $nl + $append + $nl
}

[IO.File]::WriteAllText($p, $t, $u8)
Write-Output "OK replaced=$done nl=$($nl.Length)"
