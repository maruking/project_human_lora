@echo off
chcp 65001 >nul
setlocal
call "%~dp0_common.bat"
if errorlevel 1 (
    echo [ERROR] Failed to initialize environment.
    exit /b 1
)

echo ==============================================================================
echo [STEP 02] Technical Image Metrics (Measurement Only)
echo Input, STEP1 expected frame count, output CSV and summary JSON follow below.
echo Strict current-generation measurement; any decode or integrity error fails this STEP.
echo ==============================================================================

%PY_CMD% "%PROJECT_DIR%scripts\score_blur.py" %*
if errorlevel 1 (
    echo.
    echo [ERROR] Technical measurement failed with exit code %errorlevel%.
    exit /b %errorlevel%
)

echo.
echo [SUCCESS] STEP 02: Technical metrics completed successfully.
exit /b 0
