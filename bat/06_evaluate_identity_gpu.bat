@echo off
setlocal
call "%~dp0_common.bat"
if errorlevel 1 (
    echo [ERROR] Failed to initialize environment.
    exit /b 1
)

echo ==============================================================================
echo [STEP 06] [GPU] Identity Similarity and Imposter / Distance Filtering
echo Reference: %PROJECT_DIR%input\reference\
echo Target   : %PROJECT_DIR%work\frames_raw\
echo Output   : %PROJECT_DIR%output\reports\step6_identity_scores.json
echo Review   : %PROJECT_DIR%work\identity_review\
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
