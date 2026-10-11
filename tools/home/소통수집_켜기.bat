@echo off
chcp 65001 >nul
rem 데이터 압축지도 - 서초 둘레 통행속도 수집 켜기 (2026-10-11 Claude Code 작성)
rem 하는 일: 10분마다 ITS 실시간 소통을 한 번 받아 data\traffic-snap-seocho.json 만 커밋·푸시하는 예약 작업을 등록한다.
rem 월 한도 10,000건 가운데 약 4,400건을 쓴다. 끄려면 소통수집_끄기.bat
cd /d "%~dp0..\.."
schtasks /Create /TN "datamap-traffic-snap" /TR "powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command \"Set-Location '%CD%'; py -3.12 -X utf8 tools\signal\trafficsnap.py --commit *>> '..\07_API키\out\tdata\trafficsnap.log'\"" /SC MINUTE /MO 10 /F
echo.
echo 켰다. 이 PC 가 켜져 있는 동안 10분마다 받아 지도에 올린다.
echo 기록: ..\07_API키\out\tdata\trafficsnap.log
pause
