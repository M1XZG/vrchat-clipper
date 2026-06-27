@echo off
setlocal
cd /d "%~dp0"

set "PYTHON_CMD=py -3"
%PYTHON_CMD% --version >nul 2>&1
if errorlevel 1 set "PYTHON_CMD=python"

if not exist ".venv\Scripts\python.exe" (
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 exit /b %errorlevel%
)

if not exist ".venv\.requirements-installed" (
    ".venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
    if errorlevel 1 exit /b %errorlevel%
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt --quiet
    if errorlevel 1 exit /b %errorlevel%
    copy /y requirements.txt ".venv\.requirements-installed" >nul
) else (
    fc /b requirements.txt ".venv\.requirements-installed" >nul 2>&1
    if errorlevel 1 (
        ".venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
        if errorlevel 1 exit /b %errorlevel%
        ".venv\Scripts\python.exe" -m pip install -r requirements.txt --quiet
        if errorlevel 1 exit /b %errorlevel%
        copy /y requirements.txt ".venv\.requirements-installed" >nul
    )
)

".venv\Scripts\python.exe" -m vrchat_clipper
