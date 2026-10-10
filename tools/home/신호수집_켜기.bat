@echo off
chcp 65001 >nul
rem 데이터 압축지도 - 방향별 신호 수집 켜기 (2026-10-10 Claude Code 작성)
rem 하는 일: 수집기 둘을 띄우고, 30분마다 살아 있는지 보고 죽었으면 다시 띄우는 예약 작업을 등록한다.
rem 끄려면 신호수집_끄기.bat
cd /d "%~dp0..\.."
powershell -NoProfile -ExecutionPolicy Bypass -File tools\signal\sweep-run.ps1
schtasks /Create /TN "datamap-signal-sweep" /TR "powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File \"%CD%\tools\signal\sweep-run.ps1\"" /SC MINUTE /MO 30 /F
echo.
echo 켰다. 이 PC 가 켜져 있는 동안 5분마다 받아 15분마다 지도에 올린다.
echo 기록: ..\07_API키\out\tdata\sweep_t.log , sweep_p.log
pause
