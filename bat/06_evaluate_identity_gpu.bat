@echo off
chcp 65001 >nul
setlocal
for %%I in ("%~dp0..") do set "PROJECT_DIR=%%~fI\"
set "STEP6_PY=%PROJECT_DIR%.venv-step6\Scripts\python.exe"
if not exist "%STEP6_PY%" (
    echo [ERROR] STEP6 environment missing. Run setup_step6_identity.bat first.
    exit /b 1
)
set "PYTHONPATH=%PROJECT_DIR%;%PROJECT_DIR%scripts"
echo [STEP 06] InsightFace Identity Verification v2
"%STEP6_PY%" -X utf8 "%PROJECT_DIR%scripts\step6_identity_v2.py" %*
if errorlevel 1 (
    echo [ERROR] STEP6 stopped. Inspect the error above.
    exit /b 1
)
echo [SUCCESS] STEP6 requested phase completed.
exit /b 0
