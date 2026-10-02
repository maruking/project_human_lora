@echo off
rem ==============================================================================
rem Common Environment Initialization for Pipeline BAT Files
rem ==============================================================================

rem Resolve PROJECT_DIR as the parent of this bat folder
for %%I in ("%~dp0..") do set "PROJECT_DIR=%%~fI\"

rem Set UTF-8 encoding for Unicode/Japanese filenames and terminal logs
chcp 65001 >nul

rem Auto-detect Python executable
set "PY_CMD="

rem 1. Check local virtual environment if present
if exist "%PROJECT_DIR%.venv\Scripts\python.exe" (
    set "PY_CMD="%PROJECT_DIR%.venv\Scripts\python.exe""
    goto :python_found
)
if exist "%PROJECT_DIR%venv\Scripts\python.exe" (
    set "PY_CMD="%PROJECT_DIR%venv\Scripts\python.exe""
    goto :python_found
)

rem 2. Check py launcher (prefer 3.10 for MediaPipe stability, fallback to py -3)
where py >nul 2>nul
if %errorlevel%==0 (
    py -3.10 --version >nul 2>nul
    if %errorlevel%==0 (
        set "PY_CMD=py -3.10"
        goto :python_found
    )
    py -3 --version >nul 2>nul
    if %errorlevel%==0 (
        set "PY_CMD=py -3"
        goto :python_found
    )
)

rem 3. Check system python in PATH
where python >nul 2>nul
if %errorlevel%==0 (
    set "PY_CMD=python"
    goto :python_found
)

echo [ERROR] No suitable Python executable found!
echo Please install Python (recommended 3.10) and ensure it is added to PATH.
exit /b 1

:python_found
rem Configure PYTHONPATH to include project root, scripts, and local package directories
set "PYTHONPATH=%PROJECT_DIR%;%PROJECT_DIR%scripts;%PROJECT_DIR%.step4_packages;%PYTHONPATH%"
exit /b 0
