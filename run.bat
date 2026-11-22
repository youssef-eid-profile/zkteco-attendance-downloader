@echo off
REM ==========================================================================
REM  ZKTeco Attendance Downloader - run from source (no .exe needed)
REM --------------------------------------------------------------------------
REM  Double-click this file (or run it from a terminal) on a Windows machine.
REM  It finds the best available Python (3.8 - 3.15), installs
REM  PyQt5/pyzk/openpyxl if they are missing, and runs the GUI script.
REM
REM  PyQt5's cp38-abi3 wheel has been confirmed to load on Python 3.13 - 3.15
REM  on Windows, so all of those versions are accepted. If your specific
REM  install fails with "DLL load failed", fall back to Python 3.12 from
REM  https://www.python.org/downloads/
REM
REM  For a standalone .exe instead, use build_exe.bat.
REM ==========================================================================

setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo === ZKTeco Attendance Downloader - run from source ===
echo.

set "PYEXE="

REM --- 1. Locate Python 3.8 - 3.15 (newest first) --------------------------
REM  Order: py launcher (3.15 -> 3.8), then common install dirs (same order),
REM         then python on PATH (but reject the Microsoft Store stub).

REM (a) py launcher - try each minor version, newest first
for %%V in (3.15 3.14 3.13 3.12 3.11 3.10 3.9 3.8) do (
    if not defined PYEXE (
        py -%%V -c "import sys; print(sys.executable)" >"%TEMP%\pyprobe_%%V.txt" 2>nul
        if not errorlevel 1 (
            for /f "delims=" %%P in ('type "%TEMP%\pyprobe_%%V.txt" 2^>nul') do (
                set "PYEXE=%%P"
                set "PYVER=%%V"
            )
        )
        if exist "%TEMP%\pyprobe_%%V.txt" del /q "%TEMP%\pyprobe_%%V.txt" >nul 2>nul
    )
)

REM (b) Scan common install locations, newest first
if not defined PYEXE (
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
        if not defined PYEXE (
            if exist "%%~P" (
                set "PYEXE=%%~P"
                set "PYVER=manual-scan"
            )
        )
    )
)

REM (c) Last resort: python on PATH, but reject the Microsoft Store stub.
if not defined PYEXE (
    where python >nul 2>nul
    if not errorlevel 1 (
        python -c "import sys; print(sys.executable)" >"%TEMP%\pypath_probe.txt" 2>nul
        if not errorlevel 1 (
            REM Reject Microsoft Store stub
            findstr /r /c:"\\AppData\\Local\\Microsoft\\WindowsApps" "%TEMP%\pypath_probe.txt" >nul 2>nul
            if errorlevel 1 (
                for /f "delims=" %%P in ('type "%TEMP%\pypath_probe.txt" 2^>nul') do (
                    set "PYEXE=%%P"
                    set "PYVER=PATH"
                )
            )
        )
        if exist "%TEMP%\pypath_probe.txt" del /q "%TEMP%\pypath_probe.txt" >nul 2>nul
    )
)

if not defined PYEXE (
    echo.
    echo [ERROR] No Python was found on this machine.
    echo.
    echo  Install Python 3.12 (or newer) from:
    echo    https://www.python.org/downloads/
    echo  and TICK "Add python.exe to PATH" during setup, then run this again.
    echo.
    echo  If you see "Python was not found; run without arguments to install
    echo  from the Microsoft Store" - that is the Windows Store stub. Turn OFF
    echo  python.exe / python3.exe in:
    echo    Settings -> Apps -> Advanced app settings -> App execution aliases
    echo  then run this again.
    echo.
    pause
    exit /b 1
)

echo [1/3] Using Python: %PYEXE%
"%PYEXE%" --version
echo.

REM --- 2. Install dependencies if missing ------------------------------------
echo [2/3] Checking dependencies...
"%PYEXE%" -c "import PyQt5, zk, openpyxl" 2>nul
if errorlevel 1 (
    echo      Missing - installing PyQt5, pyzk, openpyxl...
    "%PYEXE%" -m pip install --upgrade PyQt5 pyzk openpyxl
    if errorlevel 1 (
        echo [ERROR] Dependency installation failed.
        echo         If you see "no matching distribution for PyQt5" or
        echo         "DLL load failed", install Python 3.12 from
        echo         https://www.python.org/downloads/ and run this again.
        pause
        exit /b 1
    )
) else (
    echo      All dependencies present.
)
echo.

REM --- 3. Run the GUI --------------------------------------------------------
echo [3/3] Starting GUI...
"%PYEXE%" "%~dp0zkteco_attendance_gui.py"
if errorlevel 1 (
    echo.
    echo [ERROR] The GUI exited with an error. See the message above.
    pause
)

endlocal
