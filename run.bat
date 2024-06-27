echo "Running GOA File Distribution"
@Echo off

SETLOCAL
cd "C:\Users\pa_dpashayan\Desktop\PyProjects\GOA-File-Distribution"
set FILE_PATH=%~dp0
set SCRIPT_PATH=%FILE_PATH%main.py
set VENV_PATH=%FILE_PATH%.venv

call "%VENV_PATH%\Scripts\activate.bat"
python -u "%SCRIPT_PATH%"

IF ERRORLEVEL 1 (
    echo Python script encountered an error. The error message is:
    pause
)
ENDLOCAL