@echo off
chcp 65001 >nul
setlocal
call "%~dp0_common.bat"
if errorlevel 1 exit /b 1
rem Stored-metric diagnostic only. No restoration, model loading or STEP10.
%PY_CMD% "%PROJECT_DIR%scripts\step9_diagnostic.py" %*
if errorlevel 1 exit /b %errorlevel%
exit /b 0
