@echo off
chcp 65001 >nul
if "%~1"=="1" goto run
if "%~1"=="2" goto run
if "%~1"=="3" goto run
echo Usage: 03_best_review_round.bat 1, 2 or 3. best_rank_v2.2 starts at Round 1.
exit /b 1
:run
call "%~dp003_face_quality_gate.bat" --from-existing --review-round %~1
exit /b %errorlevel%
