@echo off
chcp 65001 >nul
setlocal
call "%~dp0_common.bat"
if errorlevel 1 (
    echo [ERROR] Failed to initialize environment.
    exit /b 1
)

echo ==============================================================================
echo [STEP 04] Pose / Face Scale Measurement v2 - Stored STEP3 Values
echo Effective input/output paths are printed by the Python step; defaults are defined in config.
echo ==============================================================================

%PY_CMD% "%PROJECT_DIR%scripts\step4_pose_composition.py" %*
if errorlevel 1 (
    echo.
    echo [ERROR] Pose classification failed with exit code %errorlevel%.
    exit /b %errorlevel%
)

echo.
echo [SUCCESS] STEP 04: Face pose classification completed successfully.
exit /b 0
