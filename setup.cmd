@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%.venv"
set "REQ_FILE=%SCRIPT_DIR%requirements.txt"

pushd "%SCRIPT_DIR%" >nul || exit /b 1

if exist "%VENV_DIR%\Scripts\python.exe" (
    set "BOOTSTRAP_PYTHON=%VENV_DIR%\Scripts\python.exe"
    goto install
)

where py >nul 2>nul
if not errorlevel 1 (
    py -3 -m venv "%VENV_DIR%" || goto fail
    set "BOOTSTRAP_PYTHON=%VENV_DIR%\Scripts\python.exe"
    goto install
)

where python >nul 2>nul
if not errorlevel 1 (
    python -m venv "%VENV_DIR%" || goto fail
    set "BOOTSTRAP_PYTHON=%VENV_DIR%\Scripts\python.exe"
    goto install
)

echo Python not found. Install Python 3 first.
goto fail

:install
"%BOOTSTRAP_PYTHON%" -m pip install --upgrade pip || goto fail
"%BOOTSTRAP_PYTHON%" -m pip install -r "%REQ_FILE%" || goto fail

echo Setup complete.
echo Run start_timer.vbs to launch without a terminal window.
popd >nul
exit /b 0

:fail
echo Setup failed.
popd >nul
exit /b 1
