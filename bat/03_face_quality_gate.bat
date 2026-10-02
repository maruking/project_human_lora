@echo off
chcp 65001 >nul
setlocal
call "%~dp0_common.bat"
if errorlevel 1 (
    echo [ERROR] Failed to initialize environment.
    exit /b 1
)

echo ==============================================================================
echo [STEP 03] Face Quality Gate (Face Sharpness, Occlusion and Beauty Filter Filter)
echo Effective input/output paths are printed by the Python step; defaults are defined in config.
echo ==============================================================================

if exist "%PROJECT_DIR%.step3_packages\mediapipe" set "PYTHONPATH=%PROJECT_DIR%.step3_packages;%PYTHONPATH%"

%PY_CMD% "%PROJECT_DIR%scripts\face_quality_gate.py" %*
if errorlevel 1 (
    echo.
    echo [ERROR] Face quality gate failed with exit code %errorlevel%.
    exit /b %errorlevel%
)

echo.
echo [SUCCESS] STEP 03: Face quality gate completed successfully.
exit /b 0
