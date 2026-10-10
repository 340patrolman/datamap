@echo off
chcp 65001 >nul
rem 데이터 압축지도 — 집 PC에서 형님이 한 번 실행(2026-10-10 · Claude Code 작성)
rem 하는 일: 최신 받기 → 국세청 소득 다시 굽기 → 강원·전북 실거래 행정동 잇기 → 집값 기준표 → 지역 저장소 올리기 → 지도 저장소 올리기
rem 단계마다 멈춘다. 이상하면 그 화면을 사진 찍어 Claude Code 에 보여 준다.
cd /d "%~dp0..\.."

echo.
echo [0/5] 최신 코드 받기
git pull origin main || goto :err

echo.
echo [1/5] 국세청 소득 전국판 다시 굽기 (KOSIS · 1~3분)
py -3.12 -X utf8 tools\region\guTax-bake.py || goto :err
echo   확인: 맨 끝에 "못 이음" 줄이 없어야 한다. 제물포구·영종구·서해구·검단구·세종시가 빠지면 사진.
pause

echo.
echo [2/5] 강원·전북 실거래를 좌표로 행정동에 잇기 (home-bake build · 몇 분)
if not exist "..\13_관할경계\원자료\hjd20260701.geojson" echo   주의: 행정동 경계 파일이 없다 - 동 잇기를 건너뛴다. 사진 찍어 알려 줄 것.
py -3.12 -X utf8 tools\region\home-bake.py build || goto :err
echo   확인: 끝 줄의 "좌표로 행정동 이음" 숫자(수천 개면 정상) · "행정동 못 찾음" 숫자
pause

echo.
echo [3/5] 시도·시군구 집값 기준표 다시
py -3.12 -X utf8 tools\region\homeref-bake.py || goto :err
echo   확인: 51(강원)·52(전북) 줄 끝에 'cx' 가 없어졌으면 성공

echo.
echo [4/5] 강원·전북 지역 저장소 올리기 (GitHub 로그인 필요)
gh auth status >nul 2>&1 || gh auth login
py -3.12 -X utf8 tools\region\publish-data.py push 51 52 || goto :err

echo.
echo [5/5] 지도 저장소에 자료 올리기 (열쇠 검사 먼저)
git add data\gu-tax.json data\home-ref.json
py -3.12 -X utf8 tools\keycheck.py || goto :err
git commit -m "data: 국세청 소득 인천 개편·세종 잇기 · 강원·전북 동 실거래(좌표→행정동) · 집값 기준표"
git push origin main || goto :err

echo.
echo 끝. Claude Code 에 "집 배치 끝" 이라고 알려 주면 결과를 확인한다.
pause
exit /b 0

:err
echo.
echo 멈춤 - 위 오류 화면을 사진 찍어 Claude Code 에 보여 준다. (열쇠가 화면에 보이면 가리고)
pause
exit /b 1
