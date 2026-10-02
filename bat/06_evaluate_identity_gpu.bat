@echo off
chcp 65001 >nul
setlocal
call "%~dp0_common.bat"
if errorlevel 1 (
    echo [ERROR] Failed to initialize environment.
    exit /b 1
)

echo ==============================================================================
echo [STEP 06] [GPU] Identity Similarity and Imposter / Distance Filtering
echo Effective input/output paths are printed by the Python step; defaults are defined in config.
echo Effective input/output paths are printed by the Python step; defaults are defined in config.
echo Effective input/output paths are printed by the Python step; defaults are defined in config.
echo Effective input/output paths are printed by the Python step; defaults are defined in config.
echo ==============================================================================

%PY_CMD% "%PROJECT_DIR%scripts\evaluate_identity.py" %*
if errorlevel 1 (
    echo.
    echo [ERROR] Identity evaluation failed with exit code %errorlevel%.
    exit /b %errorlevel%
)

echo.
echo [SUCCESS] STEP 06: Identity evaluation completed successfully.
exit /b 0
