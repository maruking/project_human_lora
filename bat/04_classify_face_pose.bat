@echo off
setlocal
call "%~dp0_common.bat"
if errorlevel 1 (
    echo [ERROR] Failed to initialize environment.
    exit /b 1
)

echo ==============================================================================
echo [STEP 04] Face Pose Classification (Yaw, Pitch, Roll and Composition Quota)
echo Target: %PROJECT_DIR%work\frames_raw\
echo Output: %PROJECT_DIR%output\reports\step4_pose_classified_scores.json
echo ==============================================================================

%PY_CMD% "%PROJECT_DIR%scripts\classify_face_pose.py" %*
if errorlevel 1 (
    echo.
    echo [ERROR] Pose classification failed with exit code %errorlevel%.
    exit /b %errorlevel%
)

echo.
echo [SUCCESS] STEP 04: Face pose classification completed successfully.
exit /b 0
