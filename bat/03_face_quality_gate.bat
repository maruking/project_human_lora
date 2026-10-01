@echo off
setlocal
call "%~dp0_common.bat"
if errorlevel 1 (
    echo [ERROR] Failed to initialize environment.
    exit /b 1
)

echo ==============================================================================
echo [STEP 03] Face Quality Gate (Face Sharpness, Occlusion and Beauty Filter Filter)
echo Target: %PROJECT_DIR%work\frames_raw\
echo Output: %PROJECT_DIR%output\reports\step3_face_quality_scores.json
echo Review: %PROJECT_DIR%work\facegate_review\
echo ==============================================================================

%PY_CMD% "%PROJECT_DIR%scripts\face_quality_gate.py" %*
if errorlevel 1 (
    echo.
    echo [ERROR] Face quality gate failed with exit code %errorlevel%.
    exit /b %errorlevel%
)

echo.
echo [SUCCESS] STEP 03: Face quality gate completed successfully.
exit /b 0
