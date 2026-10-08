@echo off
chcp 65001 >nul
setlocal
call "%~dp0_common.bat"
if errorlevel 1 (
    echo [ERROR] Failed to initialize environment.
    exit /b 1
)

echo ==============================================================================
echo [STEP 07] BEST Quality and Coverage Review Pool v2.2 BASE + Coverage additions
echo Review options only. STEP8 Human Review decides final inclusion.
echo Effective input/output paths are printed by the Python step; defaults are defined in config.
echo ==============================================================================

%PY_CMD% "%PROJECT_DIR%scripts\step7_candidate_selection_v22.py" %*
if errorlevel 1 (
    echo.
    echo [ERROR] Candidate selection failed with exit code %errorlevel%.
    exit /b %errorlevel%
)

echo.
echo [SUCCESS] STEP 07: Candidate selection completed successfully.
exit /b 0
