# 데이터 압축지도 — 방향별 신호 수집 지킴이(2026-10-10 · 소유자 「계속 다운을 받도록 하고」)
#   돌고 있지 않으면 띄운다: ① 잔여시간 훑기 ② 신호 상태 훑기(2분 30초 늦게 — 두 API 의 5분 제한이 따로라 번갈아)
#   Claude Code 세션이 꺼져 있어도 돈다(이 PC 가 켜져 있는 동안) · 15분마다 data/sigdir-seoul.json 만 자동 커밋·푸시(열쇠 검사 통과 때만)
#   켜기 = tools\home\신호수집_켜기.bat · 끄기 = tools\home\신호수집_끄기.bat · 기록 = ..\07_API키\out\tdata\sweep_t.log · sweep_p.log
param([switch]$Stop)
$ErrorActionPreference = 'SilentlyContinue'
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$log = Join-Path (Split-Path -Parent $root) '07_API키\out\tdata'
$all = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*spat-bake.py*sweep*' -and $_.Name -notlike 'powershell*' -and $_.Name -notlike 'bash*' }
if ($Stop) {
  $all | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
  Write-Output ("멈춤 " + @($all).Count + "개")
  exit 0
}
$hasP = @($all | Where-Object { $_.CommandLine -like '*--api p*' }).Count
$hasT = @($all | Where-Object { $_.CommandLine -notlike '*--api p*' }).Count
$base = @('-3.12', '-X', 'utf8', '-u', 'tools\signal\spat-bake.py', 'sweep', '--list', '..\07_API키\out\tdata\list_near.txt')
if (-not $hasT) {
  Start-Process -WindowStyle Hidden -FilePath 'py' -ArgumentList $base -WorkingDirectory $root -RedirectStandardOutput (Join-Path $log 'sweep_t.log') -RedirectStandardError (Join-Path $log 'sweep_t.err')
  Write-Output '잔여시간 훑기를 띄웠다'
}
if (-not $hasP) {
  if (-not $hasT) { Start-Sleep -Seconds 150 }
  # 기다리는 사이 다른 지킴이가 이미 띄웠으면 그만둔다(2026-10-10 다시 띄우다 상태 훑기가 둘이 됐다)
  $dup = @(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*spat-bake.py*sweep*--api p*' -and $_.Name -notlike 'powershell*' -and $_.Name -notlike 'bash*' }).Count
  if ($dup) { Write-Output '신호 상태 훑기는 이미 돌고 있다'; exit 0 }
  Start-Process -WindowStyle Hidden -FilePath 'py' -ArgumentList ($base + @('--api', 'p')) -WorkingDirectory $root -RedirectStandardOutput (Join-Path $log 'sweep_p.log') -RedirectStandardError (Join-Path $log 'sweep_p.err')
  Write-Output '신호 상태 훑기를 띄웠다'
}
if ($hasT -and $hasP) { Write-Output '둘 다 돌고 있다' }
