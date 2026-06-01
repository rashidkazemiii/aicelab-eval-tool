import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout,
    QVBoxLayout, QPushButton, QLabel, QStackedWidget,
    QButtonGroup, QSizePolicy,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from gui.theme import DARK_STYLESHEET
from gui.tabs.upload_tab import UploadTab
from gui.tabs.analysis_tab import AnalysisTab
from gui.tabs.history_tab import HistoryTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ICELAB Friction Evaluation Tool")
        self.setMinimumSize(1280, 800)
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ------------------------------------------------------------------
        # Sidebar
        # ------------------------------------------------------------------
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(185)
        sidebar.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(10, 20, 10, 20)
        sb_layout.setSpacing(4)

        logo = QLabel("FRICTION LAB")
        logo.setStyleSheet(
            "color: #4cceac; font-size: 15px; font-weight: bold; "
            "letter-spacing: 1px; padding: 6px 0px 14px 4px;"
        )
        sb_layout.addWidget(logo)

        self._nav_group = QButtonGroup(self)
        self._nav_group.setExclusive(True)

        self._stack = QStackedWidget()

        # Tabs defined here; upload callback switches to Analysis tab
        self._analysis_tab = AnalysisTab(self)
        self._history_tab  = HistoryTab(self)
        self._upload_tab   = UploadTab(self._switch_to_analysis, self)

        pages = [
            ("  Upload Data",  self._upload_tab),
            ("  Analysis",     self._analysis_tab),
            ("  History",      self._history_tab),
        ]
        self._nav_btns = []
        for label, page in pages:
            self._stack.addWidget(page)
            btn = QPushButton(label)
            btn.setObjectName("nav_btn")
            btn.setCheckable(True)
            btn.setFixedHeight(38)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            self._nav_group.addButton(btn)
            self._nav_btns.append(btn)
            sb_layout.addWidget(btn)

        self._nav_btns[0].setChecked(True)

        sb_layout.addStretch()

        # Version label
        ver = QLabel("v1.0")
        ver.setStyleSheet("color: #4a5568; font-size: 10px;")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sb_layout.addWidget(ver)

        root.addWidget(sidebar)
        root.addWidget(self._stack)

        # Connect nav buttons
        for idx, btn in enumerate(self._nav_btns):
            btn.clicked.connect(lambda checked, i=idx: self._switch_tab(i))

        # Refresh history when switching to it
        self._nav_btns[2].clicked.connect(self._history_tab.refresh)

    def _switch_tab(self, index: int):
        self._stack.setCurrentIndex(index)
        for i, btn in enumerate(self._nav_btns):
            btn.setChecked(i == index)

    def _switch_to_analysis(self):
        self._switch_tab(1)


def launch():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(DARK_STYLESHEET)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
