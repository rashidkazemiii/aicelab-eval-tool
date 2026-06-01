from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from database import SessionLocal, PerCycle, Result, Test


class CyclesDialog(QDialog):
    def __init__(self, test_id: int, parent=None):
        super().__init__(parent)
        self.test_id = test_id
        self.setWindowTitle(f"Per-Cycle Data — Test #{test_id}")
        self.resize(950, 500)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        db = SessionLocal()
        try:
            test   = db.query(Test).filter(Test.id == self.test_id).first()
            cycles = db.query(PerCycle).filter(PerCycle.test_id == self.test_id).all()
            result = db.query(Result).filter(Result.test_id == self.test_id).first()
        finally:
            db.close()

        title = QLabel(
            f"File: {test.file_name}  |  Type: {test.data_type}  |  "
            f"Cycles: {len(cycles)}"
        )
        title.setStyleSheet("font-weight: bold; color: #4cceac; margin-bottom: 6px;")
        layout.addWidget(title)

        per_cycle_headers = [
            "Cycle", "Static CoF Time", "Static CoF",
            "Dynamic CoF Time", "Dynamic CoF",
            "Std Dev", "N Points", "Sigma", "Variance",
        ]
        agg_headers = []
        agg_values  = []
        if result:
            agg_headers = [
                "Time Range", "Static Mean", "Static SD", "Static N",
                "Static Sum", "Static Var",
                "Dynamic Mean", "Dynamic SD", "Dynamic N",
                "Dynamic Sum", "Dynamic Var",
            ]
            agg_values = [
                result.time_range,
                result.static_mean_cof, result.static_sd, result.static_n,
                result.static_sum, result.static_variance,
                result.dynamic_mean_cof, result.dynamic_sd, result.dynamic_n,
                result.dynamic_sum, result.dynamic_variance,
            ]

        all_headers = per_cycle_headers + ([""] + agg_headers if agg_headers else [])
        n_pc = len(per_cycle_headers)

        table = QTableWidget(len(cycles), len(all_headers))
        table.setHorizontalHeaderLabels(all_headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        table.verticalHeader().setDefaultSectionSize(22)
        table.setAlternatingRowColors(True)
        table.setStyleSheet(
            "QTableWidget::item:alternate { background-color: #1a2535; }"
            "font-family: 'Consolas', monospace; font-size: 11px;"
        )

        # Colour the header sections
        for col_idx in range(n_pc):
            item = table.horizontalHeaderItem(col_idx)
            if item:
                item.setBackground(QColor("#1f2a40"))
        if agg_headers:
            for col_idx in range(n_pc + 1, len(all_headers)):
                item = table.horizontalHeaderItem(col_idx)
                if item:
                    item.setBackground(QColor("#263348"))

        def _cell(val):
            if val is None:
                return QTableWidgetItem("")
            try:
                text = f"{float(val):.5f}"
            except (ValueError, TypeError):
                text = str(val)
            item = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            return item

        for row_idx, cycle in enumerate(cycles):
            pc_vals = [
                cycle.cycle_index,
                cycle.static_cof_time, cycle.static_cof,
                cycle.dynamic_cof_time, cycle.dynamic_cof,
                cycle.dynamic_sd, cycle.dynamic_n,
                cycle.dynamic_sigma, cycle.dynamic_variance,
            ]
            for col_idx, val in enumerate(pc_vals):
                table.setItem(row_idx, col_idx, _cell(val))

            # Aggregate (only on first row)
            if row_idx == 0 and agg_values:
                for j, val in enumerate(agg_values):
                    table.setItem(row_idx, n_pc + 1 + j, _cell(val))

        layout.addWidget(table)

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)
