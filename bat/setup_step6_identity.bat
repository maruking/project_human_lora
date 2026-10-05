@echo off
chcp 65001 >nul
setlocal
for %%I in ("%~dp0..") do set "PROJECT_DIR=%%~fI\"
if not exist "%PROJECT_DIR%.venv-step6\Scripts\python.exe" (
    py -3.10 -m pip install --user virtualenv
    if errorlevel 1 exit /b 1
    py -3.10 -m virtualenv "%PROJECT_DIR%.venv-step6"
    if errorlevel 1 exit /b 1
)
"%PROJECT_DIR%.venv-step6\Scripts\python.exe" -m pip install -r "%PROJECT_DIR%requirements-step6.txt" -c "%PROJECT_DIR%requirements-step6.lock.txt"
if errorlevel 1 exit /b 1
"%PROJECT_DIR%.venv-step6\Scripts\python.exe" -m pip check
exit /b %errorlevel%
