# 用 .NET ClientWebSocket 试探火山 TTS WebSocket 鉴权
$ErrorActionPreference = "Stop"

$cfg = Get-Content "C:\Users\21674\.openclaw\openclaw.json" -Raw | ConvertFrom-Json
$key = $cfg.models.providers.minimax.apiKey
if ($key -isnot [string]) { $key = $key.value }

# 尝试用 ARK key（图片代理那把）
$arkKey = $null
$cfg2 = Get-Content "C:\Users\21674\.openclaw\openclaw.json" -Raw | ConvertFrom-Json
foreach ($p in $cfg2.models.providers.PSObject.Properties) {
    if ($p.Name -match 'volc|ark|doubao') {
        $v = $p.Value.apiKey
        if ($v -is [string]) { $arkKey = $v; Write-Output "found provider: $($p.Name)" }
    }
}
if (-not $arkKey) { Write-Output "no ark provider key in config" }

$useKey = if ($arkKey) { $arkKey } else { $key }

$uri = [Uri]"wss://openspeech.bytedance.com/api/v3/tts/bidirection"
$ws = New-Object System.Net.WebSockets.ClientWebSocket
$ws.Options.SetRequestHeader("X-Api-Key", $useKey)
$ws.Options.SetRequestHeader("X-Api-Resource-Id", "seed-tts-2.0")
$ws.Options.SetRequestHeader("X-Api-Connect-Id", [guid]::NewGuid().ToString())

$cts = New-Object System.Threading.CancellationTokenSource
$cts.CancelAfter(15000)

try {
    $ws.ConnectAsync($uri, $cts.Token).Wait()
    Write-Output "CONNECTED state=$($ws.State)"
} catch {
    Write-Output "CONNECT FAILED: $($_.Exception.Message)"
    if ($_.Exception.InnerException) { Write-Output "inner: $($_.Exception.InnerException.Message)" }
} finally {
    try { $ws.Dispose() } catch {}
}
