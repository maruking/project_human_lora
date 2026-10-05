@echo off
chcp 65001 >nul
setlocal
call "%~dp0_common.bat"
if errorlevel 1 exit /b 1
%PY_CMD% "%PROJECT_DIR%scripts\copy_step3_reject_review.py" %*
exit /b %errorlevel%
