@echo off
setlocal

echo.
echo  Banking CRM Agent
echo  =================
echo.

:: Resolve project root to the directory this script lives in
set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"

:: ── 1. Check GROQ_API_KEY ─────────────────────────────────────────────────────
if not exist "%ROOT%\backend\.env" (
    echo  [ERROR] backend\.env not found.
    echo          Create it and add: GROQ_API_KEY=your_key_here
    pause
    exit /b 1
)

findstr /i "GROQ_API_KEY" "%ROOT%\backend\.env" >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] GROQ_API_KEY not set in backend\.env
    pause
    exit /b 1
)

:: ── 2. Start backend ──────────────────────────────────────────────────────────
echo  [1/3] Starting backend  (FastAPI on :8000) ...
start "Banking CRM - Backend" cmd /k "cd /d "%ROOT%" && backend\venv\Scripts\activate && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

:: ── 3. Start frontend ─────────────────────────────────────────────────────────
echo  [2/3] Starting frontend (Vite on :3000) ...
start "Banking CRM - Frontend" cmd /k "cd /d "%ROOT%\frontend" && npm run dev"

:: ── 4. Wait for backend to be ready, then open browser ───────────────────────
echo  [3/3] Waiting for backend to be ready ...
set /a tries=0
:wait_loop
    set /a tries+=1
    if %tries% gtr 30 (
        echo  [WARN] Backend did not respond after 30s — opening browser anyway.
        goto open_browser
    )
    ping -n 2 127.0.0.1 >nul 2>&1
    powershell -Command "try { Invoke-WebRequest http://localhost:8000/docs -UseBasicParsing -TimeoutSec 1 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
    if errorlevel 1 goto wait_loop

:open_browser
echo  Opening http://localhost:3000 ...
start "" "http://localhost:3000"

echo.
echo  Both servers are running in separate windows.
echo  Frontend : http://localhost:3000
echo  Backend  : http://localhost:8000
echo  API Docs : http://localhost:8000/docs
echo.
echo  Close the server windows (or press Ctrl+C in each) to stop.
echo.
endlocal
