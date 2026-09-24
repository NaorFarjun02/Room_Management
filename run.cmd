@echo off
rem Run the Room Manager app (Windows).
rem Finds Python and starts run_app.py, which asks to install missing libraries and shows any other error.
rem
rem Usage:  double click run.cmd, or run it from CMD

setlocal
set "ROOT=%~dp0"

rem the project virtual env first, then the system Python.
rem every option is checked by really running it (the Windows Store "python" shortcut exists but doesn't run)
if exist "%ROOT%.venv\Scripts\python.exe" (
    "%ROOT%.venv\Scripts\python.exe" --version >nul 2>nul
    if not errorlevel 1 (
        "%ROOT%.venv\Scripts\python.exe" "%ROOT%run_app.py" %*
        goto :end
    )
    echo WARNING: the project virtual env .venv does not run - looking for another Python.
)
py -3 --version >nul 2>nul
if not errorlevel 1 (
    py -3 "%ROOT%run_app.py" %*
    goto :end
)
python --version >nul 2>nul
if not errorlevel 1 (
    python "%ROOT%run_app.py" %*
    goto :end
)
echo ERROR: Python was not found. Install Python 3 from https://www.python.org
echo (check "Add python.exe to PATH" in the installer) and run this script again.
cmd /c exit 1

:end
rem keep the window open on an error, so the message can be read when the script was started by double click
set "CODE=%ERRORLEVEL%"
if not "%CODE%"=="0" (
    echo.
    pause
)
endlocal & exit /b %CODE%
