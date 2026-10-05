@echo off
chcp 65001 >nul
setlocal
call "%~dp0_common.bat"
if errorlevel 1 exit /b 1
%PY_CMD% "%PROJECT_DIR%scripts\build_step3_all_images_report.py" %*
exit /b %errorlevel%
