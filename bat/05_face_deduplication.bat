@echo off
chcp 65001 >nul
setlocal
call "%~dp0_common.bat"
if errorlevel 1 (
    echo [ERROR] Failed to initialize environment.
    exit /b 1
)

echo ==============================================================================
echo [STEP 05] Deduplication v2 - Full Audit / BEST Representatives
echo Effective input/output paths are printed by the Python step; defaults are defined in config.
echo ==============================================================================

%PY_CMD% "%PROJECT_DIR%scripts\step5_dedup_v2.py" %*
if errorlevel 1 (
    echo.
    echo [ERROR] Deduplication failed with exit code %errorlevel%.
    exit /b %errorlevel%
)

echo.
echo [SUCCESS] STEP 05: Requested operation completed. Check Python publication status above.
exit /b 0
