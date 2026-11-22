"""
ZKTeco Attendance Downloader - PyQt5 GUI
========================================

A desktop GUI that connects to a ZKTeco fingerprint/face device over the
network (pyzk library), downloads attendance records for a given date
range, and exports them to:

  * `.dat`  - tab-separated text file (same format as the original script).
  * `.xlsx` - Microsoft Excel spreadsheet with a header row.

Editable fields : Device IP, Start date, End date
Read-only       : Port (4370), Password (0),
                  Start time (00:00:00), End time (23:59:59)
Background      : download runs in a QThread so the GUI never freezes
Persistent log  : every step and every error is written to an in-app log
                  panel AND to a file next to the executable, so nothing
                  is ever lost when a popup is dismissed.

Run:
    python zkteco_attendance_gui.py
"""

import os
import sys
import traceback
import subprocess
import platform
from datetime import datetime, time as dtime

from PyQt5.QtCore import Qt, QThread, pyqtSignal, QDate
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QFormLayout, QHBoxLayout,
    QLineEdit, QDateEdit, QPushButton, QLabel, QProgressBar,
    QFileDialog, QComboBox, QMessageBox, QGroupBox, QSizePolicy,
    QPlainTextEdit, QFrame
)
from PyQt5.QtGui import QFont, QTextCursor

from zk import ZK
from openpyxl import Workbook


# ----------------------------------------------------------------------------
# Default values
# ----------------------------------------------------------------------------
DEFAULT_IP = "0.0.0.0"
DEFAULT_PORT = 4370
DEFAULT_PASSWORD = 0
# Default date range: last ~3 weeks. Time component is fixed/readonly.
DEFAULT_START_DATE = QDate.currentDate().addDays(-21)
DEFAULT_END_DATE = QDate.currentDate()
FIXED_START_TIME = dtime(0, 0, 0)     # 00:00:00 - read only
FIXED_END_TIME = dtime(23, 59, 59)    # 23:59:59 - read only


# ----------------------------------------------------------------------------
# Background worker thread
# ----------------------------------------------------------------------------
class DownloadWorker(QThread):
    """Connects to the device, fetches attendance logs and writes the files.

    Emits:
        log(str, str)       - (level, message)  level in {info, ok, warn, err}
        busy(bool)          - True = start indeterminate progress animation
        finished_ok(str)    - summary message on success
        error(str)          - error message on failure
    """

    log = pyqtSignal(str, str)
    busy = pyqtSignal(bool)
    finished_ok = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, ip, port, password, start_dt, end_dt,
                 out_dat, out_xlsx, force_udp=False, parent=None):
        super().__init__(parent)
        self.ip = ip
        self.port = int(port)
        self.password = int(password)
        self.start_dt = start_dt
        self.end_dt = end_dt
        self.out_dat = out_dat
        self.out_xlsx = out_xlsx
        self.force_udp = force_udp

    def _log(self, level, msg):
        # Also write to stdout so it shows up when launched from a terminal
        # and gets captured by PyInstaller's noconsole redirect if any.
        print("[{}] {}".format(level.upper(), msg), flush=True)
        self.log.emit(level, msg)

    def run(self):
        conn = None
        try:
            self.busy.emit(True)
            proto = "UDP" if self.force_udp else "TCP"
            self._log("info", "Connecting to {}:{} (password={}, protocol={}, ommit_ping=True)…".format(
                self.ip, self.port, self.password, proto))

            # NOTE: pyzk's keyword is spelled 'ommit_ping' (two m's, ONE t).
            # The original standalone script had a typo 'omitt_ping' which
            # pyzk 0.9 rejects with TypeError — that was the root cause of
            # downloads silently failing. Fixed here.
            #
            # Protocol: many ZKTeco devices only speak UDP. If you see
            # "TCP packet invalid" with TCP, switch to UDP.
            zk = ZK(self.ip, port=self.port, timeout=15,
                    password=self.password, force_udp=self.force_udp,
                    ommit_ping=True)
            conn = zk.connect()
            self._log("ok", "Connected. Disabling device for live capture…")
            conn.disable_device()

            self._log("info", "Downloading attendance logs (this can take a few seconds)…")
            logs = conn.get_attendance()
            self._log("ok", "Device returned {} total records.".format(len(logs)))

            self._log("info", "Filtering range {} to {}…".format(
                self.start_dt.strftime("%Y-%m-%d %H:%M:%S"),
                self.end_dt.strftime("%Y-%m-%d %H:%M:%S")))
            filtered = [a for a in logs if self.start_dt <= a.timestamp <= self.end_dt]
            filtered.sort(key=lambda a: a.timestamp)
            self._log("ok", "{} records match the date range.".format(len(filtered)))

            if not filtered:
                self._log("warn", "No records in range — output files will be empty.")

            # ---- .dat export ----------------------------------------------
            if self.out_dat:
                self._log("info", "Writing .dat → {}".format(self.out_dat))
                d = os.path.dirname(os.path.abspath(self.out_dat))
                if not os.path.isdir(d):
                    os.makedirs(d, exist_ok=True)
                with open(self.out_dat, "w", newline="") as f:
                    for a in filtered:
                        f.write(
                            "{uid}\t{ts}\t{punch}\t{status}\t0\t0\n".format(
                                uid=str(a.user_id).rjust(9),
                                ts=a.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                                punch=a.punch,
                                status=a.status,
                            )
                        )
                size = os.path.getsize(self.out_dat)
                self._log("ok", "Wrote {} ({} bytes).".format(self.out_dat, size))

            # ---- .xlsx export ---------------------------------------------
            if self.out_xlsx:
                self._log("info", "Writing .xlsx → {}".format(self.out_xlsx))
                d = os.path.dirname(os.path.abspath(self.out_xlsx))
                if not os.path.isdir(d):
                    os.makedirs(d, exist_ok=True)
                wb = Workbook()
                ws = wb.active
                ws.title = "Attendance"
                ws.append(["User ID", "Timestamp", "Punch", "Status"])
                for a in filtered:
                    ws.append([
                        str(a.user_id),
                        a.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        a.punch,
                        a.status,
                    ])
                widths = [12, 20, 8, 8]
                for i, w in enumerate(widths, start=1):
                    col = ws.cell(row=1, column=i).column_letter
                    ws.column_dimensions[col].width = w
                wb.save(self.out_xlsx)
                size = os.path.getsize(self.out_xlsx)
                self._log("ok", "Wrote {} ({} bytes).".format(self.out_xlsx, size))

            self.busy.emit(False)
            self.finished_ok.emit(
                "Saved {n} of {total} records".format(n=len(filtered), total=len(logs))
            )
        except Exception as e:
            self.busy.emit(False)
            tb = traceback.format_exc()
            self._log("err", "FAILED: {}".format(e))
            self._log("err", tb)
            self.error.emit("{}\n\n{}".format(e, tb))
        finally:
            if conn is not None:
                try:
                    conn.enable_device()
                    self._log("info", "Re-enabled device.")
                except Exception:
                    pass
                try:
                    conn.disconnect()
                    self._log("info", "Disconnected.")
                except Exception:
                    pass


# ----------------------------------------------------------------------------
# Test-connection worker (does not download anything, just probes)
# ----------------------------------------------------------------------------
class TestConnectionWorker(QThread):
    """Probes the device with the chosen protocol. Emits one of:
       finished_ok(str)  - connected, returns device firmware + serial
       error(str)         - the exception message
    """

    log = pyqtSignal(str, str)
    finished_ok = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, ip, port, password, force_udp=False, parent=None):
        super().__init__(parent)
        self.ip = ip
        self.port = int(port)
        self.password = int(password)
        self.force_udp = force_udp

    def _log(self, level, msg):
        print("[{}] {}".format(level.upper(), msg), flush=True)
        self.log.emit(level, msg)

    def run(self):
        conn = None
        try:
            proto = "UDP" if self.force_udp else "TCP"
            self._log("info", "Testing {} {}:{} (password={})…".format(
                proto, self.ip, self.port, self.password))
            zk = ZK(self.ip, port=self.port, timeout=8,
                    password=self.password, force_udp=self.force_udp,
                    ommit_ping=True)
            conn = zk.connect()
            self._log("ok", "Connected ({}).".format(proto))
            # Read a couple of cheap identifying fields.
            info_bits = []
            try:
                fw = conn.get_firmware_version()
                info_bits.append("firmware={}".format(fw))
            except Exception as e:
                self._log("warn", "get_firmware_version failed: {}".format(e))
            try:
                serial = conn.get_serialnumber()
                info_bits.append("serial={}".format(serial))
            except Exception as e:
                self._log("warn", "get_serialnumber failed: {}".format(e))
            summary = "Connected via {}. {}".format(proto, ", ".join(info_bits))
            self.finished_ok.emit(summary)
        except Exception as e:
            tb = traceback.format_exc()
            self._log("err", "Test failed: {}".format(e))
            self._log("err", tb)
            self.error.emit("Could not connect via {}: {}\n\n"
                            "Tip: try the other protocol "
                            "(switch TCP ↔ UDP in the GUI).".format(proto, e))
        finally:
            if conn is not None:
                try:
                    conn.enable_device()
                except Exception:
                    pass
                try:
                    conn.disconnect()
                except Exception:
                    pass


# ----------------------------------------------------------------------------
# Main window
# ----------------------------------------------------------------------------
class MainWindow(QWidget):

    LOG_COLORS = {
        "info": "#003366",
        "ok":   "#1a7a1a",
        "warn": "#996600",
        "err":  "#cc0000",
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ZKTeco Attendance Downloader")
        self.resize(720, 640)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        # ---- Device group ----------------------------------------------
        dev_box = QGroupBox("Device")
        dev_form = QFormLayout(dev_box)
        dev_form.setLabelAlignment(Qt.AlignRight)

        self.ip_edit = QLineEdit(DEFAULT_IP)
        self.ip_edit.setPlaceholderText("e.g. 192.168.1.201")

        self.port_edit = QLineEdit(str(DEFAULT_PORT))
        self.port_edit.setReadOnly(True)
        self.port_edit.setStyleSheet("background-color: #f0f0f0;")

        self.password_edit = QLineEdit(str(DEFAULT_PASSWORD))
        self.password_edit.setReadOnly(True)
        self.password_edit.setStyleSheet("background-color: #f0f0f0;")

        # Protocol selector: TCP (default) or UDP.
        # Many ZKTeco devices only speak UDP and fail with
        # "TCP packet invalid" when you try TCP. If TCP fails, switch to UDP.
        self.proto_combo = QComboBox()
        self.proto_combo.addItems(["TCP (default)", "UDP (try if TCP fails)"])
        self.proto_combo.setToolTip(
            "Most ZKTeco devices speak UDP on port 4370. pyzk defaults to "
            "TCP. If you get 'TCP packet invalid', switch to UDP.")

        dev_form.addRow("Device IP:", self.ip_edit)
        dev_form.addRow("Port:", self.port_edit)
        dev_form.addRow("Password:", self.password_edit)
        dev_form.addRow("Protocol:", self.proto_combo)

        # Test-connection button (probes without downloading anything).
        self.test_btn = QPushButton("Test connection")
        self.test_btn.setToolTip(
            "Connect to the device with the current settings and report "
            "the firmware + serial. Does NOT download attendance data.")
        self.test_btn.clicked.connect(self.on_test_connection)
        dev_form.addRow("", self.test_btn)

        root.addWidget(dev_box)

        # ---- Date range group ------------------------------------------
        date_box = QGroupBox("Date range")
        date_form = QFormLayout(date_box)
        date_form.setLabelAlignment(Qt.AlignRight)

        # Start: date editable, time fixed & read-only shown next to it.
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(DEFAULT_START_DATE)
        self.start_time_label = QLabel("00:00:00")
        self.start_time_label.setStyleSheet(
            "color: #555; background-color: #f0f0f0; "
            "padding: 2px 8px; border: 1px solid #ccc;")

        # End: date editable, time fixed & read-only shown next to it.
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(DEFAULT_END_DATE)
        self.end_time_label = QLabel("23:59:59")
        self.end_time_label.setStyleSheet(
            "color: #555; background-color: #f0f0f0; "
            "padding: 2px 8px; border: 1px solid #ccc;")

        start_row = QHBoxLayout()
        start_row.addWidget(self.start_date_edit, 1)
        start_row.addWidget(QLabel("time:"))
        start_row.addWidget(self.start_time_label)
        start_row.addStretch(1)
        start_w = QWidget(); start_w.setLayout(start_row)

        end_row = QHBoxLayout()
        end_row.addWidget(self.end_date_edit, 1)
        end_row.addWidget(QLabel("time:"))
        end_row.addWidget(self.end_time_label)
        end_row.addStretch(1)
        end_w = QWidget(); end_w.setLayout(end_row)

        date_form.addRow("Start:", start_w)
        date_form.addRow("End:",   end_w)
        root.addWidget(date_box)

        # ---- Output group ----------------------------------------------
        out_box = QGroupBox("Output")
        out_form = QFormLayout(out_box)
        out_form.setLabelAlignment(Qt.AlignRight)

        self.format_combo = QComboBox()
        self.format_combo.addItems([
            "Both (.dat + .xlsx)",
            "Only .dat",
            "Only .xlsx",
        ])

        # Default output base path = next to the exe/script (so files are
        # easy to find), with a fallback to the user's home.
        if getattr(sys, "frozen", False):
            here = os.path.dirname(sys.executable)
        else:
            here = os.path.dirname(os.path.abspath(__file__))
        self.default_out_dir = here
        self.path_edit = QLineEdit(os.path.join(here, "1_attlog"))

        self.browse_btn = QPushButton("Browse…")
        self.browse_btn.clicked.connect(self.on_browse)
        path_row = QHBoxLayout()
        path_row.addWidget(self.path_edit, 1)
        path_row.addWidget(self.browse_btn)
        path_w = QWidget(); path_w.setLayout(path_row)

        out_form.addRow("Format:", self.format_combo)
        out_form.addRow("Output path:", path_w)
        root.addWidget(out_box)

        # ---- Action row ------------------------------------------------
        action_row = QHBoxLayout()
        self.download_btn = QPushButton("Download")
        self.download_btn.setMinimumHeight(36)
        f = QFont(); f.setBold(True); self.download_btn.setFont(f)
        self.download_btn.clicked.connect(self.on_download)

        self.open_folder_btn = QPushButton("Open output folder")
        self.open_folder_btn.setMinimumHeight(36)
        self.open_folder_btn.setEnabled(False)
        self.open_folder_btn.clicked.connect(self.on_open_folder)

        action_row.addWidget(self.download_btn, 1)
        action_row.addWidget(self.open_folder_btn)
        action_w = QWidget(); action_w.setLayout(action_row)
        root.addWidget(action_w)

        # ---- Progress --------------------------------------------------
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        root.addWidget(self.progress)

        # ---- Log panel (persistent) -----------------------------------
        log_box = QGroupBox("Log")
        log_lay = QVBoxLayout(log_box)
        log_lay.setContentsMargins(8, 8, 8, 8)
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(2000)  # keep memory bounded
        font = QFont("Consolas"); font.setStyleHint(QFont.Monospace)
        self.log_view.setFont(font)
        self.log_view.setFrameShape(QFrame.NoFrame)
        log_lay.addWidget(self.log_view)

        clear_btn = QPushButton("Clear log")
        clear_btn.clicked.connect(lambda: self.log_view.clear())
        log_lay.addWidget(clear_btn)
        root.addWidget(log_box, 1)

        # Initial greeting
        self._append_log("info", "Ready. Fill in the device IP and date range, then click Download.")

        self.worker = None
        self.test_worker = None
        self.last_out_dir = None

    # ---- helpers ----------------------------------------------------------
    def _append_log(self, level, msg):
        color = self.LOG_COLORS.get(level, "#000000")
        ts = datetime.now().strftime("%H:%M:%S")
        # HTML so we can color by level.
        safe = (msg.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                  .replace("\n", "<br>"))
        self.log_view.appendHtml(
            '<span style="color:#888;">{ts}</span> '
            '<span style="color:{color};">{msg}</span>'.format(
                ts=ts, color=color, msg=safe))
        self.log_view.moveCursor(QTextCursor.End)

    def _set_running(self, running):
        self.download_btn.setEnabled(not running)
        self.open_folder_btn.setEnabled(False)
        self.test_btn.setEnabled(not running)
        self.ip_edit.setEnabled(not running)
        self.proto_combo.setEnabled(not running)
        self.start_date_edit.setEnabled(not running)
        self.end_date_edit.setEnabled(not running)
        self.path_edit.setEnabled(not running)
        self.browse_btn.setEnabled(not running)
        self.format_combo.setEnabled(not running)

    # ---- handlers --------------------------------------------------------
    def on_browse(self):
        cur = self.path_edit.text().strip()
        d = os.path.dirname(cur) if cur else self.default_out_dir
        if not d:
            d = os.path.expanduser("~")
        chosen, _ = QFileDialog.getSaveFileName(
            self, "Select output file", d,
            "Output base name (*.dat *.xlsx);;All files (*)")
        if chosen:
            if chosen.lower().endswith((".dat", ".xlsx")):
                chosen = os.path.splitext(chosen)[0]
            self.path_edit.setText(chosen)

    def on_download(self):
        ip = self.ip_edit.text().strip()
        if not ip or ip == "0.0.0.0":
            QMessageBox.warning(self, "Missing IP",
                "Please enter the device IP (e.g. 192.168.1.201).")
            return

        try:
            port = int(self.port_edit.text())
            password = int(self.password_edit.text())
        except ValueError:
            QMessageBox.warning(self, "Bad input",
                "Port and Password must be integers.")
            return

        start_qd = self.start_date_edit.date()
        end_qd = self.end_date_edit.date()
        if start_qd > end_qd:
            QMessageBox.warning(self, "Date range",
                "Start date must be on or before End date.")
            return

        # Combine editable date with fixed read-only time.
        start_dt = datetime(start_qd.year(), start_qd.month(), start_qd.day(),
                            FIXED_START_TIME.hour, FIXED_START_TIME.minute,
                            FIXED_START_TIME.second)
        end_dt = datetime(end_qd.year(), end_qd.month(), end_qd.day(),
                          FIXED_END_TIME.hour, FIXED_END_TIME.minute,
                          FIXED_END_TIME.second)

        base = self.path_edit.text().strip()
        if not base:
            QMessageBox.warning(self, "Missing output",
                "Please choose an output path.")
            return
        base = os.path.abspath(base)
        self.path_edit.setText(base)  # show absolute path to the user

        fmt = self.format_combo.currentIndex()
        out_dat = base + ".dat" if fmt in (0, 1) else None
        out_xlsx = base + ".xlsx" if fmt in (0, 2) else None

        self.last_out_dir = os.path.dirname(base)

        self._set_running(True)
        self.progress.setRange(0, 0)  # indeterminate / busy
        proto = "UDP" if self.proto_combo.currentIndex() == 1 else "TCP"
        self._append_log("info", "─── New download started ───")
        self._append_log("info", "IP        : {}:{}".format(ip, port))
        self._append_log("info", "Protocol : {}".format(proto))
        self._append_log("info", "Date range: {} → {}".format(
            start_dt.strftime("%Y-%m-%d %H:%M:%S"),
            end_dt.strftime("%Y-%m-%d %H:%M:%S")))
        if out_dat: self._append_log("info", "Will write: {}".format(out_dat))
        if out_xlsx: self._append_log("info", "Will write: {}".format(out_xlsx))

        self.worker = DownloadWorker(
            ip=ip, port=port, password=password,
            start_dt=start_dt, end_dt=end_dt,
            out_dat=out_dat, out_xlsx=out_xlsx,
            force_udp=(self.proto_combo.currentIndex() == 1),
        )
        self.worker.log.connect(self._append_log)
        self.worker.busy.connect(self.on_busy)
        self.worker.finished_ok.connect(self.on_finished_ok)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def on_test_connection(self):
        """Probe the device with the chosen protocol without downloading."""
        ip = self.ip_edit.text().strip()
        if not ip or ip == "0.0.0.0":
            QMessageBox.warning(self, "Missing IP",
                "Please enter the device IP (e.g. 192.168.1.201) before testing.")
            return
        try:
            port = int(self.port_edit.text())
            password = int(self.password_edit.text())
        except ValueError:
            QMessageBox.warning(self, "Bad input",
                "Port and Password must be integers.")
            return

        force_udp = (self.proto_combo.currentIndex() == 1)
        proto = "UDP" if force_udp else "TCP"
        self._append_log("info", "─── Testing connection ({}) ───".format(proto))
        self._set_running(True)
        self.progress.setRange(0, 0)

        self.test_worker = TestConnectionWorker(
            ip=ip, port=port, password=password, force_udp=force_udp)
        self.test_worker.log.connect(self._append_log)
        self.test_worker.finished_ok.connect(self.on_test_ok)
        self.test_worker.error.connect(self.on_test_error)
        self.test_worker.start()

    def on_test_ok(self, msg):
        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        self._append_log("ok", "TEST OK: {}".format(msg))
        self._set_running(False)
        QMessageBox.information(self, "Connection OK", msg +
            "\n\nYou can now click Download.")

    def on_test_error(self, msg):
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self._append_log("err", "TEST FAILED: see popup.")
        self._set_running(False)
        QMessageBox.critical(self, "Connection failed", msg +
            "\n\nThe full log is preserved in the Log panel below.")

    def on_busy(self, busy):
        self.progress.setRange(0, 0) if busy else self.progress.setRange(0, 100)

    def on_finished_ok(self, msg):
        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        self._append_log("ok", "DONE: {}".format(msg))
        self._set_running(False)
        self.open_folder_btn.setEnabled(True)
        QMessageBox.information(self, "Download complete", msg +
            "\n\nSee the log panel for full details.")

    def on_error(self, msg):
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self._append_log("err", "Download failed. Full error is in the log panel above and in the popup.")
        self._set_running(False)
        # Show the popup but the log already has the full traceback, so the
        # info survives even if the user closes the popup.
        QMessageBox.critical(self, "Download failed",
            msg + "\n\nThe full log is preserved in the Log panel below.")

    def on_open_folder(self):
        d = self.last_out_dir or self.default_out_dir
        if not os.path.isdir(d):
            QMessageBox.warning(self, "Folder missing",
                "The output folder does not exist yet: {}".format(d))
            return
        try:
            if platform.system() == "Windows":
                os.startfile(d)  # type: ignore[attr-defined]
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", d])
            else:
                subprocess.Popen(["xdg-open", d])
        except Exception as e:
            QMessageBox.warning(self, "Cannot open folder",
                "Could not open the folder:\n{}".format(e))


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
