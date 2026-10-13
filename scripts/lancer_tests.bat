@echo off
setlocal
pushd "%~dp0.."
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m unittest discover -s tests -v
) else (
    py -3.15 -m unittest discover -s tests -v
)
set "result=%errorlevel%"
popd
pause
exit /b %result%
