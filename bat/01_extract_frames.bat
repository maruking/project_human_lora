@echo off
setlocal
call "%~dp0_common.bat"
if errorlevel 1 (
    echo [ERROR] Failed to initialize environment.
    exit /b 1
)

echo ==============================================================================
echo [STEP 01] Video Frame Extraction (50 Equidistant Segments)
echo Input : %PROJECT_DIR%input\original-mp4\
echo Output: %PROJECT_DIR%work\frames_raw\
echo ==============================================================================

%PY_CMD% "%PROJECT_DIR%scripts\extract_frames.py" %*
if errorlevel 1 (
    echo.
    echo [ERROR] Frame extraction failed with exit code %errorlevel%.
    exit /b %errorlevel%
)

echo.
echo [SUCCESS] STEP 01: Frame extraction completed successfully.
exit /b 0
