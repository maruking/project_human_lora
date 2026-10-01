@echo off
setlocal
call "%~dp0_common.bat"
if errorlevel 1 (
    echo [ERROR] Failed to initialize environment.
    exit /b 1
)

echo ==============================================================================
echo [STEP 07] Multi-Objective Candidate Selection and Quota Balancing
echo Output Dir: %PROJECT_DIR%work\selected\
echo Report    : %PROJECT_DIR%output\reports\step7_selected_candidates.json
echo ==============================================================================

%PY_CMD% "%PROJECT_DIR%scripts\score_lora_candidates.py" %*
if errorlevel 1 (
    echo.
    echo [ERROR] Candidate selection failed with exit code %errorlevel%.
    exit /b %errorlevel%
)

echo.
echo [SUCCESS] STEP 07: Candidate selection completed successfully.
exit /b 0
