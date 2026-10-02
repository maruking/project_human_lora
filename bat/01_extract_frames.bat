@echo off
chcp 65001 >nul
setlocal
call "%~dp0_common.bat"
if errorlevel 1 (
    echo [ERROR] Failed to initialize environment.
    exit /b 1
)

echo ==============================================================================
echo [STEP 01] Stable Video IDs, Copy Normalization and Duration-Aware Frame Extraction
echo Effective input/output paths are printed by the Python step; defaults are defined in config.
echo ==============================================================================

rem Preparation invokes the existing source-folder upscale BAT, then the unchanged extractor.
%PY_CMD% "%PROJECT_DIR%scripts\prepare_step1_upscale.py" %*
if errorlevel 1 (
    echo.
    echo [ERROR] Frame extraction failed with exit code %errorlevel%.
    exit /b %errorlevel%
)

echo.
echo [SUCCESS] STEP 01 operation completed. See the Python plan or summary above.
exit /b 0
