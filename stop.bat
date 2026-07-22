@echo off
title EcoMind AI - Stop All
echo.
echo Stopping all EcoMind AI servers...
echo.

:: Kill any running uvicorn processes
taskkill /f /im uvicorn.exe 2>nul
taskkill /f /fi "WINDOWTITLE eq EcoMind AI - Backend" 2>nul

:: Kill any running node/vite processes on port 5173
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5173" ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a 2>nul
)

:: Kill any running python processes on port 8000
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a 2>nul
)

echo.
echo All EcoMind AI servers stopped.
echo.
pause
