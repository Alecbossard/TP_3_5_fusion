@echo off
setlocal
pushd "%~dp0.."
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" "src\main.py" %*
) else (
    py -3.15 "src\main.py" %*
)
set "result=%errorlevel%"
popd
if not "%result%"=="0" pause
exit /b %result%
