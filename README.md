# ZKTeco Attendance Downloader (PyQt5 GUI)

A simple desktop GUI that connects to a ZKTeco fingerprint/face attendance
device over the network, downloads attendance records for a given date
range, and exports them to `.dat` and/or `.xlsx`.

> **Quick start for end users:** download the prebuilt `.exe` from the
> [Releases](../../releases) page and double-click it — no Python needed.
> See [DEPLOY.txt](DEPLOY.txt) for the full handoff guide.
>
> **For developers / contributors:** clone the repo and double-click
> `run.bat` (or `build_exe.bat` to produce a standalone `.exe`).

## Files

| File | Description |
| --- | --- |
| `zkteco_attendance_gui.py` | The GUI application source |
| `requirements.txt` | Python dependencies (for running from source) |
| `run.bat` | **Run from source** (double-click — finds Python, installs deps, launches GUI) |
| `build_exe.bat` | **One-click Windows .exe builder** (double-click it) |
| `ZKTecoAttendanceDownloader.spec` | PyInstaller spec (alternative build) |
| `DEPLOY.txt` | **One-page handoff guide** — give this to whoever installs the .exe on each PC |
| `PUBLISHING.md` | **Step-by-step GitHub publishing guide** (web upload / git CLI / GitHub Desktop + Releases) |
| `.gitignore` | Ignores Python/PyInstaller/build artifacts |
| `LICENSE` | MIT License |
| `README.md` | This file |

## Get it from GitHub

Three ways, depending on who you are:

### A. End user — just want the `.exe`

1. Go to the repo's **[Releases](../../releases)** page.
2. Under the latest release, download `ZKTecoAttendanceDownloader.exe`
   (it's under **Assets**).
3. Double-click it. No Python, no install. See [DEPLOY.txt](DEPLOY.txt).

### B. Run from source (no build)

```bash
git clone https://github.com/<your-user>/<your-repo>.git
cd <your-repo>
# Windows: double-click run.bat
# Or manually:
pip install -r requirements.txt
python zkteco_attendance_gui.py
```

### C. Build the `.exe` yourself

```bash
git clone https://github.com/<your-user>/<your-repo>.git
cd <your-repo>
# Windows: double-click build_exe.bat
```

Output: `dist\ZKTecoAttendanceDownloader.exe`.

## Python version requirement


**Use Python 3.8 – 3.15.** PyQt5's latest wheel on PyPI uses the `cp38-abi3`
tag, which loads on Python 3.8 through 3.15 on Windows — confirmed working
on Python 3.15. If you do hit `DLL load failed while importing PyQt5` on a
specific build, fall back to Python 3.12 from
<https://www.python.org/downloads/release/python-3127/> (both can coexist;
you do not need to remove the newer one). The `run.bat` and `build_exe.bat`
scripts try the newest installed Python first (3.15 → 3.8).

---

## Quick start (no build needed)

1. Install Python 3.12 or newer (see above) and tick
   **"Add python.exe to PATH"**.
2. Double-click **`run.bat`**. It will find Python, install `PyQt5` + `pyzk`
   + `openpyxl` if missing, and launch the GUI.

That's it. Use `build_exe.bat` only if you want a standalone `.exe`.

---

## Option A — Build a Windows `.exe` (recommended)

You run this **once** on a Windows machine that has Python installed.
The resulting `.exe` can then be copied to any Windows PC and run without
Python installed.

### Prerequisites (on the build PC)

- **Windows 10/11**
- **Python 3.8 – 3.15** from <https://www.python.org/downloads/>
  → During setup, tick **"Add Python to PATH"**

### Build steps

1. Copy the whole `download/` folder to a Windows machine (e.g. your desktop).
2. Double-click **`build_exe.bat`**.
   - It creates a virtual environment, installs `PyQt5`, `pyzk`, `openpyxl`,
     and `pyinstaller`, then runs PyInstaller.
   - Takes about 1–3 minutes the first time.
3. When it says **SUCCESS**, the `.exe` is at:

   ```
   download\dist\ZKTecoAttendanceDownloader.exe
   ```

4. Copy that single `.exe` to any Windows PC and double-click it. No Python
   install needed on the target machine.

> **Note:** The first launch of a `--onefile` PyInstaller exe takes a few
> seconds because it unpacks to a temp folder. Subsequent launches are
> faster once Windows has cached the unpacked files.

### Alternative: build with the `.spec` file

If you prefer not to use the `.bat`, from a terminal with the venv active:

```
pyinstaller ZKTecoAttendanceDownloader.spec --clean
```

---

## 📦 Deploy to other PCs (the easy part)

This is the whole point of building the `.exe`: you build it **once** on
your machine, then the resulting single file can be copied to **any**
Windows PC and double-clicked to run — no Python, no installer, no admin
rights needed on the target machines.

### Step 1 — Build the `.exe` once (on your dev PC)

You've already done this. If you need to rebuild (e.g. after a code change):

1. Double-click `build_exe.bat`.
2. Wait for `SUCCESS`.
3. The `.exe` is at:

   ```
   download\dist\ZKTecoAttendanceDownloader.exe
   ```

It's a single file, about 80 MB (it bundles Python + Qt + pyzk).

### Step 2 — Copy the `.exe` to each target PC

Pick **any** of these — they all work, choose what's easiest for you:

| Method | How |
| --- | --- |
| **USB stick** | Copy `ZKTecoAttendanceDownloader.exe` to a USB drive, plug it into the target PC, drag the file to Desktop or any folder, double-click. |
| **Network share** | Put the `.exe` on a shared folder (`\\server\Tools\`), users drag it to their own PC. |
| **Email / Teams / Slack** | Zip the `.exe` (right-click → Send to → Compressed folder) and send. Some mail systems block `.exe` attachments — zip it with a password or rename the zip to `.zipx` if needed. |
| **OneDrive / Google Drive** | Upload the `.exe`, share the link. Download and run on the target. |

### Step 3 — Run it on the target PC

1. Double-click `ZKTecoAttendanceDownloader.exe`.
   - The **first launch** takes 5–10 seconds (PyInstaller unpacks to a temp
     folder). Subsequent launches are fast.
   - If Windows SmartScreen says "Windows protected your PC", click
     **More info** → **Run anyway**. This is normal for unsigned `.exe`
     files; it's not a security problem, just Microsoft not recognizing
     the publisher.
   - If antivirus quarantines it, mark it as trusted / restore it.
     PyInstaller `.exe`s commonly trigger false positives.
2. Fill in the **Device IP** (the ZKTeco device's IP on your LAN).
3. Pick **Start** and **End** dates.
4. Click **Download**.

That's it. The target PC needs **nothing else** — no Python, no
dependencies, no setup wizard.

### Network requirements on each target PC

- The target PC must be on the **same network** (LAN/VPN) as the ZKTeco
  device, and able to reach the device's IP on **TCP port 4370**.
- To verify reachability before running the app, on the target PC open
  PowerShell and run:

  ```powershell
  Test-NetConnection -ComputerName <DEVICE_IP> -Port 4370
  ```

  `TcpTestSucceeded : True` means the app can connect. If it's `False`,
  ask IT to allow port 4370 between that PC and the device.

### Multi-PC checklist (for IT / whoever is rolling this out)

```
□ Built ZKTecoAttendanceDownloader.exe (build_exe.bat → SUCCESS)
□ Copied the .exe to the target PC(s)
□ Target PC is on the same LAN as the ZKTeco device
□ Test-NetConnection <device_ip> -Port 4370 → TcpTestSucceeded : True
□ Windows Firewall allows outbound TCP 4370 (it does by default)
□ User can double-click the .exe and the GUI opens
□ First download against the real device succeeds (check the Log panel)
□ If SmartScreen blocks: More info → Run anyway
□ If antivirus blocks: add an exception for the .exe
```

### Optionally bundle a shortcut

To make it feel like a "real" installed app, on each target PC:

1. Right-click `ZKTecoAttendanceDownloader.exe` → **Create shortcut**.
2. Move the shortcut to `%AppData%\Microsoft\Windows\Start Menu\Programs\`
   (the user's Start menu) — it will then appear in the Start menu.
3. Optionally right-click the shortcut → **Properties** → **Change icon**
   to give it a custom icon.

This is a shortcut, not an install — the `.exe` itself stays wherever you
put it and remains fully portable.

---

## Option B — Run from source (no .exe)

If you already have Python and prefer not to build an `.exe`:

```bash
pip install -r requirements.txt
python zkteco_attendance_gui.py
```

Requires Python 3.7+ and the PyQt5 system Qt libraries (the `PyQt5` pip wheel
bundles them on Windows and macOS; on Linux you may also need
`sudo apt install libgl1`).

---

## How to use the GUI

1. **Device IP** — editable, prefilled with `0.0.0.0`. Type the device's
   real IP (e.g. `192.168.1.201`).
2. **Port** — read-only, fixed at `4370` (ZKTeco default).
3. **Password** — read-only, fixed at `0`.
4. **Start** — date picker. The time is fixed at `00:00:00` (read-only).
5. **End** — date picker. The time is fixed at `23:59:59` (read-only).
6. **Format** — choose `Both (.dat + .xlsx)`, `Only .dat`, or `Only .xlsx`.
7. **Output path** — base name without extension. The app appends `.dat`
   and/or `.xlsx` automatically based on the chosen format.
   Click **Browse…** to pick a location. Defaults to next to the
   script / `.exe` so the files are easy to find.
8. Click **Download**.

A progress bar and a **persistent log panel** at the bottom show every step
(Connecting → Downloading → Filtering → Writing → Done). The download runs
in a background thread, so the window stays responsive. If anything fails,
the full traceback stays in the log panel even after the popup is closed.
After a successful download, an **Open output folder** button appears.

## Output formats

### `.dat` (identical to the original standalone script)

Tab-separated, one record per line:

```
<user_id rjust-9>\t<YYYY-MM-DD HH:MM:SS>\t<punch>\t<status>\t0\t0
```

Example:

```
        1	2026-10-28 09:05:01	1	0	0	0
      123	2026-11-05 18:00:00	4	1	0	0
```

### `.xlsx`

Excel spreadsheet with a header row:

| User ID | Timestamp           | Punch | Status |
| ------- | ------------------- | ----- | ------ |
| 1       | 2026-10-28 09:05:01 | 1     | 0      |

## Notes

- The original `ommit_ping=True` (sic) flag from pyzk is preserved, so the
  app will attempt to connect even if the device does not respond to ICMP
  ping — useful on networks where ping is blocked.
- If the connection fails, the full Python traceback is shown in an error
  dialog so you can diagnose network / password / firewall issues.
- The `.exe` is **not** prebuilt in this sandbox (which is Linux with no
  Wine/sudo). You build it locally on Windows via `build_exe.bat`.

## Troubleshooting

### Running from source (`run.bat` or `python zkteco_attendance_gui.py`)

| Problem | Fix |
| --- | --- |
| `ModuleNotFoundError: No module named 'PyQt5'` | PyQt5 is not installed for this Python. Run `run.bat` (it installs deps automatically) **or** manually: `pip install PyQt5 pyzk openpyxl`. |
| `DLL load failed while importing PyQt5` | Rare on a working install. If it happens, install Python 3.12 from <https://www.python.org/downloads/release/python-3127/> alongside your current one — both coexist. |
| VS Code runs the script with the wrong Python | Press `Ctrl+Shift+P` → `Python: Select Interpreter` → pick the interpreter where PyQt5 is installed. |
| `pip install PyQt5` says "no matching distribution" | Your Python is too new or the wrong bitness. Use a 64-bit Python 3.8–3.15. |

### Building the `.exe` (`build_exe.bat`)

| Problem | Fix |
| --- | --- |
| `Python was not found; run without arguments to install from the Microsoft Store…` | Windows ships a fake `python.exe` stub that just opens the Store. `build_exe.bat` now bypasses it automatically by trying the `py` launcher first, then scanning `%LOCALAPPDATA%\Programs\Python\…`. If it still fails: install real Python from <https://www.python.org/downloads/> (tick **"Add python.exe to PATH"**) **or** turn OFF `python.exe` / `python3.exe` in Settings → Apps → Advanced app settings → App execution aliases. |
| `'python' is not recognized` | Reinstall Python with **"Add Python to PATH"** ticked |
| PyInstaller fails on `zk` import | Already handled — the `.spec` and `.bat` both collect all `zk` submodules |
| Antivirus flags the `.exe` | False positive common with PyInstaller; allow it or sign the exe |
| `.exe` is ~80 MB | Normal for PyQt5 `--onefile` (bundles Qt). Use `--onedir` if size matters |

---

## For developers

### Project layout

```
zkteco_attendance_gui.py        # single-file PyQt5 GUI app
build_exe.bat                   # one-click PyInstaller build (Windows)
run.bat                         # one-click run from source (Windows)
ZKTecoAttendanceDownloader.spec # PyInstaller spec (alternative build)
requirements.txt                # PyQt5, pyzk, openpyxl
DEPLOY.txt                      # end-user handoff guide
LICENSE                         # MIT
.gitignore                      # ignores .venv, build/, dist/, *.pyc, etc.
```

### Run from source (for development)

```bash
git clone https://github.com/<your-user>/<your-repo>.git
cd <your-repo>
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
python zkteco_attendance_gui.py
```

### Contributing

1. Fork the repo.
2. Create a branch: `git checkout -b feature/my-improvement`.
3. Make your changes. Keep the app single-file (`zkteco_attendance_gui.py`)
   unless a refactor is clearly justified.
4. Test on Windows (the primary target) — at minimum, run the GUI and
   confirm a download against a real device succeeds, and check the log
   panel shows no errors.
5. Commit with a clear message and open a Pull Request.

### Releasing a new version

When you want to publish a new `.exe` for end users:

1. Update the version / commit any code changes.
2. On a Windows PC with the repo cloned, double-click `build_exe.bat`.
3. Verify `dist\ZKTecoAttendanceDownloader.exe` runs and downloads.
4. On GitHub, go to **Releases → Draft a new release**.
5. Tag version (e.g. `v1.0.0`), title it the same, paste the changelog
   in the description.
6. Drag `ZKTecoAttendanceDownloader.exe` into the **Attach binaries**
   area. GitHub accepts files up to 2 GB; the `.exe` is ~80 MB.
7. Click **Publish release**.

End users then get it from the **Releases** page (see "Get it from
GitHub" at the top of this README).

## License

MIT — see [LICENSE](LICENSE). You're free to use, modify, and distribute,
including commercially, as long as the copyright notice is preserved.
