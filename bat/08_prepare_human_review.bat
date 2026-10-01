@echo off
setlocal
call "%~dp0_common.bat"
if errorlevel 1 (
    echo [ERROR] Failed to initialize environment.
    exit /b 1
)

echo ==============================================================================
echo [STEP 08] Prepare Human Review Dashboard and Candidate Visualizer
echo Target : %PROJECT_DIR%work\selected\
echo Report : %PROJECT_DIR%output\reports\human_review_dashboard.html
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
echo   - Folder: %PROJECT_DIR%work\selected\
echo   - Review HTML: %PROJECT_DIR%output\reports\human_review_dashboard.html
echo.
echo Delete any unwanted frames directly from 'work\selected\' before proceeding
echo to Step 09 (Restoration) and Step 10 (Packaging).
echo ==============================================================================
exit /b 0
