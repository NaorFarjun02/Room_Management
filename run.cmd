@echo off
rem Run the Room Manager app.
rem If a Python library is missing, ask to install it with pip and try again (until the app starts).
rem Any other error is shown and the script stops.
rem
rem Usage:  double click run.cmd, or run it from CMD

setlocal EnableExtensions EnableDelayedExpansion

set "ROOT=%~dp0"
set "APP_DIR=%ROOT%src\1.1 - sql-UI"
set "ERR_FILE=%TEMP%\room_manager_errors_%RANDOM%.txt"
set "INSTALLED= "

rem ---------------------------------------- find python ----------------------------------------
rem every option is checked by really running it (the Windows Store "python" shortcut exists but doesn't run)
set "PY_EXE="
set "PY_ARGS="
if exist "%ROOT%.venv\Scripts\python.exe" (
    "%ROOT%.venv\Scripts\python.exe" --version >nul 2>nul
    if not errorlevel 1 (
        set "PY_EXE=%ROOT%.venv\Scripts\python.exe"
        goto :found_python
    )
    echo WARNING: the project virtual env .venv does not run - looking for another Python.
)
py -3 --version >nul 2>nul
if not errorlevel 1 (
    set "PY_EXE=py"
    set "PY_ARGS=-3"
    goto :found_python
)
python --version >nul 2>nul
if not errorlevel 1 (
    set "PY_EXE=python"
    goto :found_python
)
echo ERROR: Python was not found. Install Python 3 from https://www.python.org
echo ^(check "Add python.exe to PATH" in the installer^) and run this script again.
goto :fail

:found_python

cd /d "%APP_DIR%" 2>nul
if errorlevel 1 (
    echo ERROR: can't find the app folder: %APP_DIR%
    goto :fail
)

rem ---------------------------------------- run the app ----------------------------------------
:run
echo Starting Room Manager...
"%PY_EXE%" %PY_ARGS% main.py 2> "%ERR_FILE%"
set "CODE=%ERRORLEVEL%"
if "%CODE%"=="0" goto :done

rem "ModuleNotFoundError: No module named 'PyQt5.QtSvg'" -> PyQt5
set "MODULE="
for /f "usebackq tokens=2 delims='" %%m in (`findstr /c:"No module named" "%ERR_FILE%"`) do set "MODULE=%%m"
if defined MODULE for /f "tokens=1 delims=." %%t in ("%MODULE%") do set "MODULE=%%t"

rem a missing file of the project itself is not a library -> it's a real error
if defined MODULE if exist "!MODULE!" set "MODULE="
if defined MODULE if exist "!MODULE!.py" set "MODULE="

if not defined MODULE (
    echo.
    echo ERROR: the app stopped with an error ^(exit code %CODE%^):
    type "%ERR_FILE%"
    goto :fail
)

rem pip package name for an import name, when they are not the same
set "PACKAGE=!MODULE!"
if /i "!MODULE!"=="psycopg2" set "PACKAGE=psycopg2-binary"

rem stop if this package was already installed by the script and the library is still missing
set "ALREADY="
for %%p in (%INSTALLED%) do if /i "%%p"=="%PACKAGE%" set "ALREADY=1"
if defined ALREADY (
    echo.
    echo ERROR: '!PACKAGE!' was installed but Python still can't find the '!MODULE!' library:
    type "%ERR_FILE%"
    goto :fail
)

echo.
echo The library '!MODULE!' is missing.
set "ANSWER="
set /p "ANSWER=Install it now with: pip install !PACKAGE! ? [y/N] "
rem y / Y / yes -> install
if defined ANSWER if /i "!ANSWER:~0,1!"=="y" goto :install
echo Not installed - the app can't start without '!MODULE!'.
goto :fail

:install
"%PY_EXE%" %PY_ARGS% -m pip install !PACKAGE!
if errorlevel 1 (
    echo.
    echo ERROR: installing '!PACKAGE!' failed ^(see the pip message above^).
    goto :fail
)
set "INSTALLED=!INSTALLED!!PACKAGE! "
echo.
goto :run

rem ---------------------------------------- end ----------------------------------------
:done
del "%ERR_FILE%" >nul 2>nul
endlocal
exit /b 0

:fail
del "%ERR_FILE%" >nul 2>nul
echo.
pause
endlocal
exit /b 1
