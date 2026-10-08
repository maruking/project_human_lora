@echo off
chcp 65001 >nul
setlocal
call "%~dp0_common.bat"
if errorlevel 1 (
    echo [ERROR] Failed to initialize environment.
    exit /b 1
)

echo ==============================================================================
echo [STEP 04] Pose / Face Scale Measurement v3 - buffalo_l 3D landmarks
echo Effective input/output paths are printed by the Python step; defaults are defined in config.
echo ==============================================================================

set "STEP4_PY=%PROJECT_DIR%.venv-step6\Scripts\python.exe"
rem Keep the approved InsightFace runtime isolated from legacy STEP4 package overlays.
set "PYTHONPATH=%PROJECT_DIR%;%PROJECT_DIR%scripts"
if not exist "%STEP4_PY%" (
    echo [ERROR] Existing InsightFace environment .venv-step6 is required. No automatic installation.
    exit /b 1
)
"%STEP4_PY%" -X utf8 "%PROJECT_DIR%scripts\step4_pose_composition_v3.py" %*
if errorlevel 1 (
    echo.
    echo [ERROR] Pose classification failed with exit code %errorlevel%.
    exit /b %errorlevel%
)

echo.
echo [SUCCESS] STEP 04: Face pose classification completed successfully.
exit /b 0
