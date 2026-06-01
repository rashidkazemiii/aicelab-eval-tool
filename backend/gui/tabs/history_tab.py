from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from database import SessionLocal, Test, Result, PerCycle
from gui.dialogs.cycles_dialog import CyclesDialog

_TYPE_COLORS = {
    "OFT":     "#4cceac",
    "SRV":     "#6870fa",
    "SRV_FSA": "#f0a500",
}


class HistoryTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        header_row = QHBoxLayout()
        title = QLabel("Test History")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #4cceac;")
        btn_refresh = QPushButton("Refresh")
        btn_refresh.setFixedWidth(90)
        btn_refresh.clicked.connect(self.refresh)
        header_row.addWidget(title)
        header_row.addStretch()
        header_row.addWidget(btn_refresh)
        layout.addLayout(header_row)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "File", "Type", "Upload Date", "Parameters", "Cycles", "Actions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(
            "QTableWidget::item:alternate { background-color: #1a2535; }"
        )
        layout.addWidget(self.table)

    def refresh(self):
        db = SessionLocal()
        try:
            tests = db.query(Test).order_by(Test.uploaded_at.desc()).all()
            rows  = []
            for test in tests:
                n_cycles = db.query(PerCycle).filter(PerCycle.test_id == test.id).count()
                rows.append((test, n_cycles))
        finally:
            db.close()

        self.table.setRowCount(len(rows))
        for row_idx, (test, n_cycles) in enumerate(rows):
            self.table.setRowHeight(row_idx, 36)

            # ID
            self._set_item(row_idx, 0, str(test.id), center=True)
            # File
            self._set_item(row_idx, 1, test.file_name)
            # Type (colored chip)
            self.table.setCellWidget(row_idx, 2, _TypeChip(test.data_type))
            # Date
            date_str = test.uploaded_at.strftime("%Y-%m-%d %H:%M") if test.uploaded_at else ""
            self._set_item(row_idx, 3, date_str, center=True)
            # Parameters
            params = (
                f"filter={test.filter_window}  "
                f"static={test.static_range}%  "
                f"dyn={test.dynamic_min}–{test.dynamic_max}%"
            )
            self._set_item(row_idx, 4, params)
            # Cycles count
            self._set_item(row_idx, 5, str(n_cycles), center=True)
            # Actions
            self.table.setCellWidget(row_idx, 6, _ActionCell(test.id, self._view, self._delete))

    def _set_item(self, row, col, text, center=False):
        item = QTableWidgetItem(text)
        if center:
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, col, item)

    def _view(self, test_id: int):
        dlg = CyclesDialog(test_id, self)
        dlg.exec()

    def _delete(self, test_id: int):
        reply = QMessageBox.question(
            self, "Delete test",
            f"Delete test #{test_id} and all its data?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        db = SessionLocal()
        try:
            test = db.query(Test).filter(Test.id == test_id).first()
            if test:
                db.delete(test)
                db.commit()
        finally:
            db.close()
        self.refresh()


class _TypeChip(QWidget):
    def __init__(self, data_type: str, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        color = _TYPE_COLORS.get(data_type, "#718096")
        lbl = QLabel(data_type)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(
            f"background-color: {color}20; color: {color}; "
            f"border: 1px solid {color}; border-radius: 4px; "
            f"padding: 2px 6px; font-size: 11px; font-weight: bold;"
        )
        layout.addWidget(lbl)


class _ActionCell(QWidget):
    def __init__(self, test_id: int, view_cb, delete_cb, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(6)

        btn_view = QPushButton("View Cycles")
        btn_view.setObjectName("btn_view")
        btn_view.setFixedHeight(26)
        btn_view.clicked.connect(lambda: view_cb(test_id))

        btn_del = QPushButton("Delete")
        btn_del.setObjectName("btn_delete")
        btn_del.setFixedHeight(26)
        btn_del.clicked.connect(lambda: delete_cb(test_id))

        layout.addWidget(btn_view)
        layout.addWidget(btn_del)
        layout.addStretch()
