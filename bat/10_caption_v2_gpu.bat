@echo off
chcp 65001 >nul
setlocal
call "%~dp0_common.bat"
if errorlevel 1 exit /b 1
echo [STEP10 Caption V2] Qwen3-VL; baseline unchanged; Human Review required.
%PY_CMD% "%PROJECT_DIR%scripts\step10_caption_v2.py" %*
exit /b %errorlevel%
