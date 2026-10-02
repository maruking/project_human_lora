@echo off
chcp 65001 >nul
setlocal
call "%~dp0_common.bat"
if errorlevel 1 (
    echo [ERROR] Failed to initialize environment.
    exit /b 1
)

echo ==============================================================================
echo [STEP 08] Prepare Human Review Folder and Selection Summary
echo Effective input/output paths are printed by the Python step; defaults are defined in config.
echo Review: selected folder and console summary; HTML dashboard is planned for later STEP8
echo ==============================================================================

%PY_CMD% "%PROJECT_DIR%scripts\prepare_human_review.py" %*
if errorlevel 1 (
    echo.
    echo [ERROR] Human review preparation failed with exit code %errorlevel%.
    exit /b %errorlevel%
)

echo.
echo ==============================================================================
echo [ACTION REQUIRED] HUMAN REVIEW GATEWAY
echo Please inspect the selected candidates in:
echo Effective input/output paths are printed by the Python step; defaults are defined in config.
echo   - Inspect the selected directory printed by Step8 above.
echo.
echo Delete any unwanted frames directly from 'work\selected\' before proceeding
echo to Step 09 (Restoration) and Step 10 (Packaging).
echo ==============================================================================
exit /b 0
