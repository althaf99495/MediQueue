@echo off
if "%1"=="run" (
    venv\Scripts\python app.py
) else (
    echo Usage: make run
)
