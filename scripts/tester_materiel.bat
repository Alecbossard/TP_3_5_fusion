@echo off
setlocal
pushd "%~dp0.."
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" "scripts\tester_materiel.py" %*
) else (
    py -3.15 "scripts\tester_materiel.py" %*
)
set "result=%errorlevel%"
popd
pause
exit /b %result%
