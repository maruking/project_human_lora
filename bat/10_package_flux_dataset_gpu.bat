@echo off
chcp 65001 >nul
setlocal
call "%~dp0_common.bat"
if errorlevel 1 (
    echo [ERROR] Failed to initialize environment.
    exit /b 1
)

echo ==============================================================================
echo [STEP 10] [GPU] Final Packaging for FLUX.1 LoRA Training
echo Effective input/output paths are printed by the Python step; defaults are defined in config.
echo Effective input/output paths are printed by the Python step; defaults are defined in config.
echo ==============================================================================

%PY_CMD% "%PROJECT_DIR%scripts\package_flux_dataset.py" %*
if errorlevel 1 (
    echo.
    echo [ERROR] Dataset packaging failed with exit code %errorlevel%.
    exit /b %errorlevel%
)

echo.
echo ==============================================================================
echo [COMPLETE] Real Human LoRA Dataset is packaged and ready for training!
echo Effective input/output paths are printed by the Python step; defaults are defined in config.
echo ==============================================================================
exit /b 0
