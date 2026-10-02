@echo off
chcp 65001 >nul
setlocal
call "%~dp0_common.bat"
if errorlevel 1 (
    echo [ERROR] Failed to initialize environment.
    exit /b 1
)

echo ==============================================================================
echo  REAL HUMAN LoRA DATASET PIPELINE - AUTOMATED RUNNER
echo ==============================================================================
echo Project Directory: %PROJECT_DIR%
echo.

rem Parse command-line flags
set "SKIP_PAUSE=0"
if "%~1"=="--skip-pause" set "SKIP_PAUSE=1"
if "%~1"=="-y" set "SKIP_PAUSE=1"

echo >>> Running STEP 00: Environment Pre-flight Check...
call "%~dp000_environment_check.bat"
if errorlevel 1 goto :pipeline_error

echo.
echo >>> Running STEP 01: Normalize Video Copies and Extract Per-Video Frames...
call "%~dp001_extract_frames.bat"
if errorlevel 1 goto :pipeline_error

echo.
echo >>> Running STEP 02: Technical Metrics (Blur Score)...
call "%~dp002_technical_metrics.bat"
if errorlevel 1 goto :pipeline_error

echo.
echo >>> Running STEP 03: Face Quality Gate (Face Sharpness and Beauty Filter)...
call "%~dp003_face_quality_gate.bat"
if errorlevel 1 goto :pipeline_error

echo.
echo >>> Running STEP 04: Face Pose and Shot Composition Classification...
call "%~dp004_classify_face_pose.bat"
if errorlevel 1 goto :pipeline_error

echo.
echo >>> Running STEP 05: Redundancy Deduplication...
call "%~dp005_face_deduplication.bat"
if errorlevel 1 goto :pipeline_error

echo.
echo >>> Running STEP 06: Identity Similarity Evaluation (GPU)...
call "%~dp006_evaluate_identity_gpu.bat"
if errorlevel 1 goto :pipeline_error

echo.
echo >>> Running STEP 07: Multi-Objective Candidate Selection...
call "%~dp007_score_lora_candidates.bat"
if errorlevel 1 goto :pipeline_error

rem Revision B produces report-only proposals. Legacy STEP8 reads materialized
rem candidates and must not consume stale folders from the former STEP7 path.
echo.
echo [STOP] Revision B candidate reports are ready for Human Review.
echo STEP8-10 handoff requires a separate revision. No downstream processing was run.
exit /b 0

echo.
echo >>> Running STEP 08: Prepare Human Review Folder...
call "%~dp008_prepare_human_review.bat"
if errorlevel 1 goto :pipeline_error

echo.
echo ==============================================================================
echo [CHECKPOINT] HUMAN REVIEW GATEWAY
echo ==============================================================================
echo Step 01 - 08 have completed successfully!
echo Candidates have been selected into:
echo Effective input/output paths are printed by the Python step; defaults are defined in config.
echo Inspect the selected directory printed by Step8 above.
echo HTML dashboard is planned for a later STEP8.
echo.
echo Recommended action: Open the folder and review the images.
echo If any image is blurry, wrong person, or unwanted, delete it now.
echo ==============================================================================

if "%SKIP_PAUSE%"=="0" (
    echo.
    echo Press any key to continue to Step 09 (Restoration) and Step 10 (Packaging)...
    echo (Or press Ctrl+C to stop here and run Step 09 / 10 manually later)
    pause >nul
) else (
    echo [--skip-pause passed: Continuing directly to Step 09 and 10]
)

echo.
echo >>> Running STEP 09: Selective Face Restoration (Raw Camera Skin Preserved) (GPU)...
call "%~dp009_selective_restoration_gpu.bat"
if errorlevel 1 goto :pipeline_error

echo.
echo >>> Running STEP 10: Packaging for FLUX.1 LoRA Training (GPU)...
call "%~dp010_package_flux_dataset_gpu.bat"
if errorlevel 1 goto :pipeline_error

echo.
echo ==============================================================================
echo [PIPELINE SUCCESS] ALL STEPS COMPLETED SUCCESSFULLY!
echo ==============================================================================
echo Final Dataset Ready at:
echo Effective input/output paths are printed by the Python step; defaults are defined in config.
echo ==============================================================================
exit /b 0

:pipeline_error
echo.
echo ==============================================================================
echo [PIPELINE ABORTED] A step failed with an error. Pipeline execution halted.
echo Please inspect the error messages above.
echo ==============================================================================
exit /b 1
