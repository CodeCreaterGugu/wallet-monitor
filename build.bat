@echo off
REM wallet-monitor one-click build
REM 1) full deps  2) relink openclaw  3) build  4) prod-only deps
setlocal
cd /d "%~dp0"
set GLOBAL_OPENCLAW=C:\Users\21674\AppData\Roaming\npm\node_modules\openclaw

echo [1/4] npm install (full)
call npm install || goto :err

echo [2/4] relink node_modules\openclaw
if exist "node_modules\openclaw" rmdir /s /q "node_modules\openclaw"
mklink /J "node_modules\openclaw" "%GLOBAL_OPENCLAW%" >nul || goto :err

echo [3/4] npm run build
call npm run build || goto :err

echo [4/4] prune to production deps
rmdir /s /q node_modules
call npm install --omit=dev || goto :err

echo.
echo BUILD OK
goto :eof

:err
echo.
echo BUILD FAILED
exit /b 1