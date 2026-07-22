@echo off
title EcoMind AI Launcher
echo.
echo ========================================
echo    EcoMind AI - One Click Launcher
echo ========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not in PATH.
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

:: Install backend dependencies if needed
echo [1/4] Installing backend dependencies...
cd backend
pip install -r requirements.txt --quiet 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] Some backend packages may have failed. Continuing...
)
cd ..

:: Install frontend dependencies if needed
echo [2/4] Installing frontend dependencies...
cd frontend
call npm install --silent 2>nul
cd ..

:: Start the backend in a new window
echo [3/4] Starting Backend server...
start "EcoMind AI - Backend" cmd /k "cd backend && uvicorn app.main:app --reload"

:: Wait a moment for the backend to start
timeout /t 3 /noq >nul

:: Start the frontend in a new window
echo [4/4] Starting Frontend server...
start "EcoMind AI - Frontend" cmd /k "cd frontend && npm run dev"

:: Wait for frontend to start
timeout /t 3 /noq >nul

:: Open the browser
echo.
echo ========================================
echo    EcoMind AI is starting up!
echo ========================================
echo.
echo    Frontend:  http://localhost:5173
echo    Backend:   http://localhost:8000
echo    API Docs:  http://localhost:8000/docs
echo.
echo    Opening browser in 5 seconds...
echo    Close this window anytime.
echo    To stop: close the Backend and
echo    Frontend windows.
echo ========================================
echo.

timeout /t 5 /noq >nul
start http://localhost:5173

pause
