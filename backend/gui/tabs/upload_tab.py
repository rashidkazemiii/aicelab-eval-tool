import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QRadioButton, QButtonGroup, QFileDialog, QSizePolicy,
)
from PyQt6.QtCore import Qt, QThreadPool, QUrl
from PyQt6.QtGui import QDragEnterEvent, QDropEvent

from gui.state import app_state
from gui.workers import LoadFileWorker


class UploadTab(QWidget):
    def __init__(self, on_imported, parent=None):
        super().__init__(parent)
        self._on_imported = on_imported
        self._file_path   = None
        self._build_ui()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.setSpacing(18)

        title = QLabel("FRICTION EVALUATION TOOL")
        title.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: #4cceac; letter-spacing: 2px;"
        )
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(title)

        # Drop area
        self.drop_area = _DropArea(self._on_drop)
        self.drop_area.setFixedSize(420, 200)
        outer.addWidget(self.drop_area, alignment=Qt.AlignmentFlag.AlignCenter)

        # File type selector
        type_row = QHBoxLayout()
        type_row.setSpacing(16)
        type_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._type_group = QButtonGroup(self)
        for label in ("OFT", "SRV", "SRV_FSA"):
            rb = QRadioButton(label)
            self._type_group.addButton(rb)
            type_row.addWidget(rb)
        self._type_group.buttons()[0].setChecked(True)
        outer.addLayout(type_row)

        # File info
        self.info_frame = QFrame()
        self.info_frame.setObjectName("file_info")
        self.info_frame.hide()
        info_layout = QVBoxLayout(self.info_frame)
        info_layout.setContentsMargins(12, 8, 12, 8)
        self.lbl_fname = QLabel()
        self.lbl_fsize = QLabel()
        self.lbl_ftype = QLabel()
        for lbl in (self.lbl_fname, self.lbl_fsize, self.lbl_ftype):
            lbl.setStyleSheet("font-size: 11px; color: #a0aec0;")
            info_layout.addWidget(lbl)
        self.info_frame.setFixedWidth(420)
        outer.addWidget(self.info_frame, alignment=Qt.AlignmentFlag.AlignCenter)

        # Import button
        self.btn_import = QPushButton("Import")
        self.btn_import.setFixedSize(160, 36)
        self.btn_import.setEnabled(False)
        self.btn_import.clicked.connect(self._do_import)
        outer.addWidget(self.btn_import, alignment=Qt.AlignmentFlag.AlignCenter)

        # Status
        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet("color: #e53935; font-size: 11px;")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(self.status_lbl)

        outer.addStretch()

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_drop(self, path: str):
        self._set_file(path)

    def _pick_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open test file", "",
            "Data files (*.txt *.csv *.dat *.fsa);;All files (*)"
        )
        if path:
            self._set_file(path)

    def _set_file(self, path: str):
        self._file_path = path
        size_kb = os.path.getsize(path) / 1024
        self.lbl_fname.setText(f"File:  {os.path.basename(path)}")
        self.lbl_fsize.setText(f"Size:  {size_kb:.1f} KB")
        self.lbl_ftype.setText(f"Type:  {self._data_type()}")
        self.info_frame.show()
        self.btn_import.setEnabled(True)
        self.status_lbl.setText("")
        self.drop_area.set_filename(os.path.basename(path))

    def _data_type(self) -> str:
        checked = self._type_group.checkedButton()
        return checked.text() if checked else "OFT"

    def _do_import(self):
        if not self._file_path:
            return
        self.btn_import.setEnabled(False)
        self.status_lbl.setText("Loading…")

        worker = LoadFileWorker(self._file_path, self._data_type())
        worker.signals.finished.connect(self._on_loaded)
        worker.signals.error.connect(self._on_error)
        QThreadPool.globalInstance().start(worker)

    def _on_loaded(self):
        self.status_lbl.setText("")
        self.btn_import.setEnabled(True)
        app_state.file_loaded.emit()
        self._on_imported()

    def _on_error(self, msg: str):
        short = msg.strip().split("\n")[-1]
        self.status_lbl.setText(f"Error: {short}")
        self.btn_import.setEnabled(True)


# ---------------------------------------------------------------------------
# Drop area subwidget
# ---------------------------------------------------------------------------

class _DropArea(QFrame):
    def __init__(self, on_drop_cb, parent=None):
        super().__init__(parent)
        self._cb = on_drop_cb
        self.setObjectName("drop_area")
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(8)

        icon = QLabel("☁")
        icon.setStyleSheet("font-size: 48px; color: #3e4396;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)

        self.hint = QLabel("Drag & drop file here\nor click to browse")
        self.hint.setStyleSheet("color: #718096; font-size: 12px;")
        self.hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.hint)

    def set_filename(self, name: str):
        self.hint.setText(f"✓  {name}")
        self.hint.setStyleSheet("color: #4cceac; font-size: 12px; font-weight: bold;")

    def mousePressEvent(self, event):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open test file", "",
            "Data files (*.txt *.csv *.dat *.fsa);;All files (*)"
        )
        if path:
            self._cb(path)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            self._cb(urls[0].toLocalFile())
