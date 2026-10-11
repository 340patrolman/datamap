@echo off
chcp 65001 >nul
rem 데이터 압축지도 - 서초 둘레 통행속도 수집 끄기 (2026-10-11 Claude Code 작성)
schtasks /Delete /TN "datamap-traffic-snap" /F
echo 껐다. 지도의 방향별 막힘(열쇠 없는 사람용)은 25분 뒤부터 「오래된 값」으로 안 보인다.
pause
