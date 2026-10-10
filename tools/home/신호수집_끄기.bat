@echo off
chcp 65001 >nul
rem 데이터 압축지도 - 방향별 신호 수집 끄기
cd /d "%~dp0..\.."
schtasks /Delete /TN "datamap-signal-sweep" /F
powershell -NoProfile -ExecutionPolicy Bypass -File tools\signal\sweep-run.ps1 -Stop
echo 껐다.
pause
