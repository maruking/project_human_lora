@echo off
call "%~dp003_face_quality_gate.bat" --feedback-only %*
exit /b %errorlevel%
