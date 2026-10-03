@echo off
setlocal
echo ===================================================
echo   Starting ComicCraft AI Graphic Novel Studio...
echo ===================================================

if not exist ".env" (
    echo [.env not found, creating from .env.example...]
    copy .env.example .env
)

where py >nul 2>nul
if %errorlevel% equ 0 (
    set PY_CMD=py
) else (
    set PY_CMD=python
)

echo Using Python command: %PY_CMD%
echo.
echo Launching ComicCraft FastAPI server on http://127.0.0.1:8000
%PY_CMD% run.py

pause
