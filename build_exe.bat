@echo off
REM ==========================================================================
REM  ZKTeco Attendance Downloader - one-click Windows .exe builder
REM --------------------------------------------------------------------------
REM  Double-click this file (or run it from a terminal) on a Windows machine
REM  that has Python 3.8 - 3.15 installed.
REM
REM  It will:
REM    1. Locate a REAL Python (bypasses the Microsoft Store stub)
REM    2. Create a local virtual environment (.venv)
REM    3. Install PyQt5, pyzk, openpyxl, pyinstaller
REM    4. Run PyInstaller to build a single-file windowed .exe
REM    5. Put the result in  dist\ZKTecoAttendanceDownloader.exe
REM
REM  NOTE: PyQt5's cp38-abi3 wheel has been confirmed to load on Python
REM  3.13 - 3.15 on Windows, so all of those versions are accepted.
REM ==========================================================================

setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo === ZKTeco Attendance Downloader - .exe builder ===
echo.

set "PYEXE="

REM --- 1. Locate a REAL Python (bypass Microsoft Store stub) ----------------
REM  Strategy, in order:
REM    a) py launcher       - ships with real Python, never shadowed by Store
REM    b) common install dirs under %LOCALAPPDATA% and %ProgramFiles%
REM    c) python on PATH    - last resort (often the Store stub)

REM (a) Try the official `py` launcher
where py >nul 2>nul
if not errorlevel 1 (
    for /f "delims=" %%V in ('py -3 --version 2^>nul') do set "PYVER=%%V"
    if defined PYVER (
        for /f "delims=" %%P in ('py -3 -c "import sys; print(sys.executable)" 2^>nul') do set "PYEXE=%%P"
        if defined PYEXE goto :found_python
    )
)

REM (b) Scan common install locations (per-user first, then system-wide),
REM     newest Python first.
for %%P in (
    "%LOCALAPPDATA%\Programs\Python\Python315\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python39\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python38\python.exe"
    "%ProgramFiles%\Python315\python.exe"
    "%ProgramFiles%\Python314\python.exe"
    "%ProgramFiles%\Python313\python.exe"
    "%ProgramFiles%\Python312\python.exe"
    "%ProgramFiles%\Python311\python.exe"
    "%ProgramFiles%\Python310\python.exe"
    "%ProgramFiles%\Python39\python.exe"
    "%ProgramFiles%\Python38\python.exe"
    "%ProgramFiles(x86)%\Python315\python.exe"
    "%ProgramFiles(x86)%\Python314\python.exe"
    "%ProgramFiles(x86)%\Python313\python.exe"
    "%ProgramFiles(x86)%\Python312\python.exe"
    "%ProgramFiles(x86)%\Python311\python.exe"
    "%ProgramFiles(x86)%\Python310\python.exe"
    "%ProgramFiles(x86)%\Python39\python.exe"
    "%ProgramFiles(x86)%\Python38\python.exe"
) do (
    if exist "%%~P" (
        set "PYEXE=%%~P"
        goto :found_python
    )
)

REM (c) Last resort: python on PATH (but detect the Store stub and reject it)
where python >nul 2>nul
if not errorlevel 1 (
    REM Probe: the Store stub prints "Python was not found" or exits non-zero
    python -c "import sys; print(sys.executable)" >"%TEMP%\pyprobe.txt" 2>nul
    if not errorlevel 1 (
        for /f "delims=" %%L in ('findstr /r /c:"\\AppData\\Local\\Microsoft\\WindowsApps" "%TEMP%\pyprobe.txt" 2^>nul') do (
            echo [WARNING] The 'python' on your PATH is the Microsoft Store stub.
            echo           It cannot run real Python programs.
            set "PYEXE="
        )
        if not defined PYEXE (
            for /f "delims=" %%P in ('python -c "import sys; print(sys.executable)" 2^>nul') do set "PYEXE=%%P"
            if defined PYEXE goto :found_python
        )
    )
)

REM Nothing found.
echo.
echo [ERROR] No real Python 3.8 - 3.15 installation was found.
echo.
echo  Two ways to fix this:
echo.
echo  OPTION 1 - Install Python (recommended):
echo    1. Go to https://www.python.org/downloads/
echo    2. Download Python 3.12.x (or 3.13/3.14/3.15 - all work)
echo    3. Run the installer and TICK "Add python.exe to PATH"
echo    4. Close this window and double-click build_exe.bat again
echo.
echo  OPTION 2 - Disable the Store alias (if Python is already installed):
echo    1. Windows Settings -> Apps -> Advanced app settings ->
echo       App execution aliases
echo    2. Turn OFF the toggles for python.exe and python3.exe
echo    3. Double-click build_exe.bat again
echo.
pause
exit /b 1

:found_python
echo [1/4] Using Python: %PYEXE%
"%PYEXE%" --version
echo.

REM --- 2. Create venv (skip if already present) -----------------------------
if not exist ".venv\Scripts\python.exe" (
    echo [2/4] Creating virtual environment...
    "%PYEXE%" -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo [2/4] Virtual environment already exists, reusing it.
)

call ".venv\Scripts\activate.bat"
if not defined VIRTUAL_ENV (
    echo [ERROR] Could not activate the virtual environment.
    pause
    exit /b 1
)

REM --- 3. Install dependencies ---------------------------------------------
echo.
echo [3/4] Installing dependencies (PyQt5, pyzk, openpyxl, pyinstaller)...
python -m pip install --upgrade pip >nul
python -m pip install --upgrade PyQt5 pyzk openpyxl pyinstaller
if errorlevel 1 (
    echo [ERROR] Dependency installation failed.
    pause
    exit /b 1
)

REM --- 4. Build the .exe with PyInstaller -----------------------------------
echo.
echo [4/4] Building .exe with PyInstaller (this can take 1-3 minutes)...
REM  --noconsole = windowed app, no black cmd window
REM  --onefile   = single .exe file
REM  --clean     = clean PyInstaller cache before building
pyinstaller --noconfirm --clean --onefile --noconsole ^
    --name "ZKTecoAttendanceDownloader" ^
    --collect-all zk ^
    zkteco_attendance_gui.py
if errorlevel 1 (
    echo [ERROR] PyInstaller build failed.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  SUCCESS
echo  The .exe is at:
echo    %CD%\dist\ZKTecoAttendanceDownloader.exe
echo ============================================================
echo.
echo  You can copy that .exe to any Windows machine and run it -
echo  no Python install needed on the target PC.
echo.
pause
endlocal
