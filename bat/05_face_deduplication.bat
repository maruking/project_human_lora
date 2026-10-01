@echo off
setlocal
call "%~dp0_common.bat"
if errorlevel 1 (
    echo [ERROR] Failed to initialize environment.
    exit /b 1
)

echo ==============================================================================
echo [STEP 05] Face Redundancy Deduplication (Perceptual and Structural Hashing)
echo Output: %PROJECT_DIR%output\reports\step5_dedup_scores.json
echo ==============================================================================

%PY_CMD% "%PROJECT_DIR%scripts\face_deduplication.py" %*
if errorlevel 1 (
    echo.
    echo [ERROR] Deduplication failed with exit code %errorlevel%.
    exit /b %errorlevel%
)

echo.
echo [SUCCESS] STEP 05: Face deduplication completed successfully.
exit /b 0
