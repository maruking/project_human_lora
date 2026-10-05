@echo off
chcp 65001 >nul
setlocal
call "%~dp0_common.bat"
if errorlevel 1 (
    echo [ERROR] Failed to initialize environment.
    exit /b 1
)

echo ==============================================================================
echo [STEP 03] BEST v2.2 Ranking / Explicit Review Operations
echo Effective input/output paths are printed by the Python step; defaults are defined in config.
echo ==============================================================================

if exist "%PROJECT_DIR%.step3_packages\mediapipe" set "PYTHONPATH=%PROJECT_DIR%.step3_packages;%PYTHONPATH%"

%PY_CMD% "%PROJECT_DIR%scripts\step3_best_ranking.py" %*
if errorlevel 1 (
    echo.
    echo [ERROR] BEST ranking failed with exit code %errorlevel%.
    exit /b %errorlevel%
)

echo.
echo [SUCCESS] Requested STEP 03 operation completed. See the result and path above.
echo Ranking alone does not extract a review round. New best_rank_v2.2 review starts at Round 1.
echo These folders are disposable review outputs, never pipeline input.
exit /b 0
