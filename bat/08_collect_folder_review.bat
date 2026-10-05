@echo off
chcp 65001 >nul
setlocal
call "%~dp0_common.bat"
if errorlevel 1 exit /b 1
%PY_CMD% "%PROJECT_DIR%scripts\step8_folder_review.py" collect %*
if errorlevel 1 exit /b %errorlevel%
exit /b 0
