@echo off
chcp 65001 >nul
setlocal
call "%~dp0_common.bat"
if errorlevel 1 (
    echo [ERROR] Failed to initialize environment.
    exit /b 1
)

echo ==============================================================================
echo [STEP 07] Revision B: A/B/C Coverage-Balanced Candidate Selection
echo Report-only proposal. Human Review is required before downstream processing.
echo Effective input/output paths are printed by the Python step; defaults are defined in config.
echo ==============================================================================

%PY_CMD% "%PROJECT_DIR%scripts\select_revision_b.py" %*
if errorlevel 1 (
    echo.
    echo [ERROR] Candidate selection failed with exit code %errorlevel%.
    exit /b %errorlevel%
)

echo.
echo [SUCCESS] STEP 07: Candidate selection completed successfully.
exit /b 0
