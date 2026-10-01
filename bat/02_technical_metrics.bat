@echo off
setlocal
call "%~dp0_common.bat"
if errorlevel 1 (
    echo [ERROR] Failed to initialize environment.
    exit /b 1
)

echo ==============================================================================
echo [STEP 02] Technical Metrics Calculation (Laplacian Variance / Blur Score)
echo Target: %PROJECT_DIR%work\frames_raw\
echo Output: %PROJECT_DIR%output\reports\step2_blur_scores.json
echo ==============================================================================

%PY_CMD% "%PROJECT_DIR%scripts\score_blur.py" %*
if errorlevel 1 (
    echo.
    echo [ERROR] Blur scoring failed with exit code %errorlevel%.
    exit /b %errorlevel%
)

echo.
echo [SUCCESS] STEP 02: Technical metrics completed successfully.
exit /b 0
