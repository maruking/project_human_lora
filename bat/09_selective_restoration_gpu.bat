@echo off
chcp 65001 >nul
setlocal
call "%~dp0_common.bat"
if errorlevel 1 (
    echo [ERROR] Failed to initialize environment.
    exit /b 1
)

echo ==============================================================================
echo [STEP 09] [GPU] Selective Face Restoration (Raw Camera Skin Preserved)
echo Effective input/output paths are printed by the Python step; defaults are defined in config.
echo Effective input/output paths are printed by the Python step; defaults are defined in config.
echo ==============================================================================

%PY_CMD% "%PROJECT_DIR%scripts\selective_restoration.py" %*
if errorlevel 1 (
    echo.
    echo [ERROR] Selective restoration failed with exit code %errorlevel%.
    exit /b %errorlevel%
)

echo.
echo [SUCCESS] STEP 09: Selective restoration completed successfully.
exit /b 0
