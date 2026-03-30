import sys
import subprocess
import re
import json
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QSystemTrayIcon, QMenu, QAction,
    QScrollArea
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QIcon, QColor, QPainter, QPixmap

# ── Load config ────────────────────────────────────────────
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

def load_colors():
    try:
        with open(CONFIG_PATH) as f:
            return json.load(f)["colors"]
    except Exception:
        return {}

C = load_colors()
BG      = C.get("bg",      "#1e2a1f")
SURFACE = C.get("surface", "#243325")
BORDER  = C.get("border",  "#346739")
ACCENT  = C.get("accent",  "#79AE6F")
LIGHT   = C.get("light",   "#9FCB98")
TEXT    = C.get("text",    "#F2EDC2")
SUBTEXT = C.get("subtext", "#79AE6F")
RED     = C.get("red",     "#c0614a")
# ───────────────────────────────────────────────────────────


def run(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout.strip()
    except Exception:
        return False, ""


def is_running(check):
    ok, _ = run(check)
    return ok


def port_info(port):
    _, out = run(f"ss -tlnp | grep ':{port} '")
    if not out:
        return None
    match = re.search(r'users:\(\("([^"]+)"', out)
    return match.group(1) if match else "unknown"


def dot_pixmap(color, size=10):
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QColor(color))
    p.setPen(Qt.NoPen)
    p.drawEllipse(0, 0, size, size)
    p.end()
    return pix


SECTIONS = [
    {
        "title": "XAMPP",
        "services": [
            {
                "name": "XAMPP",
                "subtitle": "Apache + MySQL",
                "check": "ss -tlnp | grep -q ':80 '",
                "start": "sudo /opt/lampp/lampp start",
                "stop":  "sudo /opt/lampp/lampp stop",
            },
            {
                "name": "Apache",
                "subtitle": "XAMPP only",
                "check": "ss -tlnp | grep -q ':80 '",
                "start": "sudo /opt/lampp/bin/apachectl start",
                "stop":  "sudo /opt/lampp/bin/apachectl stop",
            },
            {
                "name": "MySQL",
                "subtitle": "XAMPP only",
                "check": "ss -tlnp | grep -q ':3306 '",
                "start": "sudo /opt/lampp/lampp startmysql",
                "stop":  "sudo /opt/lampp/lampp stopmysql",
            },
        ],
    },
    {
        "title": "System Services",
        "services": [
            {
                "name": "Apache2",
                "subtitle": "System",
                "check": "systemctl is-active --quiet apache2",
                "start": "sudo systemctl start apache2",
                "stop":  "sudo systemctl stop apache2",
            },
            {
                "name": "MySQL",
                "subtitle": "System",
                "check": "systemctl is-active --quiet mysql",
                "start": "sudo systemctl start mysql",
                "stop":  "sudo systemctl stop mysql",
            },
        ],
    },
    {
        "title": "Databases",
        "services": [
            {
                "name": "PostgreSQL",
                "subtitle": "port 5432",
                "check": "systemctl is-active --quiet postgresql",
                "start": "sudo systemctl start postgresql",
                "stop":  "sudo systemctl stop postgresql",
            },
            {
                "name": "MongoDB",
                "subtitle": "port 27017",
                "check": "systemctl is-active --quiet mongod",
                "start": "sudo systemctl start mongod",
                "stop":  "sudo systemctl stop mongod",
            },
            {
                "name": "Redis",
                "subtitle": "port 6379",
                "check": "systemctl is-active --quiet redis",
                "start": "sudo systemctl start redis",
                "stop":  "sudo systemctl stop redis",
            },
        ],
    },
]

PORTS = [80, 443, 3306, 5432, 6379, 27017]


class ServiceCard(QFrame):
    def __init__(self, service):
        super().__init__()
        self.service = service
        self.setStyleSheet(f"""
            QFrame {{
                background: {SURFACE};
                border-radius: 8px;
                border: 1px solid {BORDER};
            }}
        """)
        self.setFixedHeight(48)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)

        self.dot = QLabel()
        self.dot.setFixedSize(10, 10)
        layout.addWidget(self.dot)

        text = QVBoxLayout()
        text.setSpacing(1)
        name = QLabel(service["name"])
        name.setStyleSheet(f"color: {TEXT}; font-weight: bold; font-size: 12px; border: none;")
        sub = QLabel(service["subtitle"])
        sub.setStyleSheet(f"color: {SUBTEXT}; font-size: 10px; border: none;")
        text.addWidget(name)
        text.addWidget(sub)
        layout.addLayout(text)
        layout.addStretch()

        self.start_btn = QPushButton("Start")
        self.stop_btn  = QPushButton("Stop")
        for btn, color in [(self.start_btn, LIGHT), (self.stop_btn, RED)]:
            btn.setFixedSize(52, 24)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {color}; color: {BG};
                    border-radius: 5px; font-weight: bold;
                    font-size: 10px; border: none;
                }}
                QPushButton:disabled {{ background: {BORDER}; color: {SUBTEXT}; }}
            """)
            layout.addWidget(btn)

        self.start_btn.clicked.connect(self.start)
        self.stop_btn.clicked.connect(self.stop)
        self.refresh()

    def refresh(self):
        running = is_running(self.service["check"])
        self.dot.setPixmap(dot_pixmap(LIGHT if running else RED))
        self.start_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)

    def start(self):
        subprocess.Popen(self.service["start"], shell=True)
        QTimer.singleShot(2000, self.refresh)

    def stop(self):
        subprocess.Popen(self.service["stop"], shell=True)
        QTimer.singleShot(2000, self.refresh)


class CollapsibleSection(QWidget):
    def __init__(self, title, services):
        super().__init__()
        self.expanded = True
        self.cards = []

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self.toggle_btn = QPushButton(f"▾  {title}")
        self.toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background: {BORDER};
                color: {TEXT};
                border-radius: 8px;
                font-weight: bold;
                font-size: 11px;
                padding: 7px 12px;
                text-align: left;
                border: none;
            }}
            QPushButton:hover {{ background: {ACCENT}; color: {BG}; }}
        """)
        self.toggle_btn.clicked.connect(self.toggle)
        self._layout.addWidget(self.toggle_btn)

        self.content = QWidget()
        self.content.setContentsMargins(0, 0, 0, 0)
        cl = QVBoxLayout(self.content)
        cl.setContentsMargins(0, 5, 0, 0)
        cl.setSpacing(4)

        for svc in services:
            card = ServiceCard(svc)
            cl.addWidget(card)
            self.cards.append(card)

        self._layout.addWidget(self.content)

    def toggle(self):
        self.expanded = not self.expanded
        self.content.setVisible(self.expanded)
        # Remove height reservation when collapsed
        if self.expanded:
            self.content.setMaximumHeight(16777215)
            self.setMaximumHeight(16777215)
        else:
            self.content.setMaximumHeight(0)
        arrow = "▾" if self.expanded else "▸"
        title = self.toggle_btn.text()[3:]
        self.toggle_btn.setText(f"{arrow}  {title}")

    def refresh(self):
        for card in self.cards:
            card.refresh()


class PortsSection(QWidget):
    def __init__(self):
        super().__init__()
        self.expanded = True
        self.rows = []

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self.toggle_btn = QPushButton("▾  Ports")
        self.toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background: {BORDER};
                color: {TEXT};
                border-radius: 8px;
                font-weight: bold;
                font-size: 11px;
                padding: 7px 12px;
                text-align: left;
                border: none;
            }}
            QPushButton:hover {{ background: {ACCENT}; color: {BG}; }}
        """)
        self.toggle_btn.clicked.connect(self.toggle)
        self._layout.addWidget(self.toggle_btn)

        self.content = QFrame()
        self.content.setStyleSheet(f"""
            QFrame {{
                background: {SURFACE};
                border-radius: 8px;
                border: 1px solid {BORDER};
            }}
        """)
        cl = QVBoxLayout(self.content)
        cl.setContentsMargins(12, 8, 12, 8)
        cl.setSpacing(5)

        for port in PORTS:
            row = QHBoxLayout()
            dot = QLabel()
            dot.setFixedSize(10, 10)
            plbl = QLabel(f":{port}")
            plbl.setFixedWidth(55)
            plbl.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 11px;")
            proc = QLabel()
            proc.setStyleSheet(f"color: {TEXT}; font-size: 11px;")
            row.addWidget(dot)
            row.addWidget(plbl)
            row.addWidget(proc)
            row.addStretch()
            cl.addLayout(row)
            self.rows.append((port, dot, proc))

        # add top margin via wrapper
        wrapper = QWidget()
        wl = QVBoxLayout(wrapper)
        wl.setContentsMargins(0, 5, 0, 0)
        wl.setSpacing(0)
        wl.addWidget(self.content)
        self._layout.addWidget(wrapper)
        self.wrapper = wrapper

        self.refresh()

    def toggle(self):
        self.expanded = not self.expanded
        self.wrapper.setVisible(self.expanded)
        if not self.expanded:
            self.wrapper.setMaximumHeight(0)
        else:
            self.wrapper.setMaximumHeight(16777215)
        self.toggle_btn.setText(f"{'▾' if self.expanded else '▸'}  Ports")

    def refresh(self):
        for port, dot, proc_lbl in self.rows:
            proc = port_info(port)
            if proc:
                dot.setPixmap(dot_pixmap(LIGHT))
                proc_lbl.setText(proc)
                proc_lbl.setStyleSheet(f"color: {TEXT}; font-size: 11px;")
            else:
                dot.setPixmap(dot_pixmap(BORDER))
                proc_lbl.setText("free")
                proc_lbl.setStyleSheet(f"color: {SUBTEXT}; font-size: 11px;")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Server Dashboard")
        self.setFixedWidth(400)
        self.setStyleSheet(f"background: {BG};")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(6)

        title = QLabel("Server Dashboard")
        title.setStyleSheet(f"color: {TEXT}; font-size: 15px; font-weight: bold; margin-bottom: 4px;")
        layout.addWidget(title)

        self.sections = []
        for sec in SECTIONS:
            s = CollapsibleSection(sec["title"], sec["services"])
            layout.addWidget(s)
            self.sections.append(s)

        self.ports = PortsSection()
        layout.addWidget(self.ports)

        footer = QLabel("Auto-refreshes every 5s  ·  edit config.json to change colors")
        footer.setStyleSheet(f"color: {BORDER}; font-size: 9px; margin-top: 4px;")
        footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer)

        layout.addStretch()

        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_all)
        self.timer.start(5000)

        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(QIcon("/usr/share/icons/Humanity/places/22/server.svg"))
        tray_menu = QMenu()
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(QApplication.quit)
        tray_menu.addAction(show_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)
        self.tray.setContextMenu(tray_menu)
        self.tray.activated.connect(lambda r: self.show() if r == QSystemTrayIcon.Trigger else None)
        self.tray.show()

    def refresh_all(self):
        for s in self.sections:
            s.refresh()
        self.ports.refresh()

    def closeEvent(self, event):
        event.ignore()
        self.hide()


if __name__ == "__main__":
    import signal
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    signal.signal(signal.SIGINT, lambda *_: app.quit())
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
