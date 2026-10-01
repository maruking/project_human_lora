@echo off
setlocal
call "%~dp0_common.bat"
if errorlevel 1 (
    echo [ERROR] Environment initialization failed in _common.bat
    exit /b 1
)

echo ========================================================
echo  [STEP 00] Environment and Hardware Check (Dry Run)
echo ========================================================

%PY_CMD% "%PROJECT_DIR%scripts\verify_environment.py" %*
set "EXIT_CODE=%errorlevel%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo [WARNING] Environment check reported issues. Exit code: %EXIT_CODE%
)

exit /b %EXIT_CODE%
