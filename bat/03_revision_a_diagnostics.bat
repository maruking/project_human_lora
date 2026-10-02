@echo off
chcp 65001 >nul
setlocal
call "%~dp0_common.bat"
if errorlevel 1 exit /b 1
if exist "%PROJECT_DIR%.step3_packages\mediapipe" set "PYTHONPATH=%PROJECT_DIR%.step3_packages;%PYTHONPATH%"
echo [MARU RUN] All formal STEP1 frames and supplemental images will be measured.
echo [SCOPE] Separate A/B/C sidecars only. Official STEP3 decisions are preserved.
%PY_CMD% "%PROJECT_DIR%scripts\step3_revision_a_diagnostics.py" %*
exit /b %errorlevel%
