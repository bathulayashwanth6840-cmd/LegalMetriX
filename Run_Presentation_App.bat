@echo off
title LegalMetriX Presentation Setup
echo ============================================================
echo Starting LegalMetriX Presentation Setup...
echo ============================================================
echo.

:: Get workspace root
set "PROJECT_ROOT=%~dp0"
cd /d "%PROJECT_ROOT%"

:: Kill any existing uvicorn backend or node servers
echo Cleaning up existing servers...
taskkill /f /im node.exe >nul 2>&1
taskkill /f /im python.exe >nul 2>&1
echo.

:: 1. Start Backend
echo [1/5] Starting Backend Server...
cd /d "%PROJECT_ROOT%\backend"
start "LegalMetriX Backend" cmd /c ".\venv\Scripts\activate.bat && uvicorn app.main:app --host 0.0.0.0 --port 8001"
echo Backend server launched in separate window.
echo.

:: 2. Start Public Tunnel
echo [2/5] Starting Public Tunnel...
if exist tunnel.log del /f /q tunnel.log
start "LegalMetriX Tunnel" /min cmd /c "ssh -o StrictHostKeyChecking=no -R 80:localhost:8001 nokey@localhost.run > tunnel.log 2>&1"

echo Waiting 6 seconds for tunnel link to establish...
timeout /t 6 >nul

:: Extract Tunnel URL from log
set "TUNNEL_URL="
for /f "tokens=4" %%a in ('findstr /C:"tunneled with" tunnel.log') do (
    set "TUNNEL_URL=%%a"
)

if "%TUNNEL_URL%"=="" (
    :: Fallback search if string format differs
    for /f "tokens=2 delims=," %%a in ('findstr /C:"https://" tunnel.log') do (
        set "TUNNEL_URL=%%a"
      )
)

:: Trim spaces and check
if "%TUNNEL_URL%"=="" (
    echo [WARNING] Tunnel URL could not be automatically parsed from log.
    echo Please check the 'tunnel.log' file to see if the connection succeeded.
    echo.
    set /p "TUNNEL_URL=Please copy and paste the HTTPS url from tunnel.log here: "
)

echo.
echo ============================================================
echo ACTIVE PUBLIC TUNNEL URL: %TUNNEL_URL%
echo ============================================================
echo.

:: 3. Rebuild Frontend
echo [3/5] Compiling production build pointing to tunnel...
cd /d "%PROJECT_ROOT%\frontend"
set VITE_API_URL=%TUNNEL_URL%
call npm run build
echo.

:: 4. Open Directories & Services
echo [4/5] Opening compiled distribution folder...
explorer.exe "%PROJECT_ROOT%\frontend\dist"

echo [5/5] Launching Netlify deployment page in browser...
start https://app.netlify.com/
start %TUNNEL_URL%

echo.
echo ===================================================================
echo SETUP COMPLETED SUCCESSFULLY!
echo ===================================================================
echo.
echo 1. Drag the 'dist' folder (which just opened in explorer) into 
echo    your Netlify site panel to update it.
echo.
echo 2. Bypass the tunnel warning on your phone:
echo    Open %TUNNEL_URL% in your mobile browser,
echo    and click "Proceed" or "Bypass".
echo.
echo 3. Log in on your phone at your Netlify site link!
echo.
echo ===================================================================
pause
