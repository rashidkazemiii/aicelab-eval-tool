from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QFileDialog, QHeaderView,
)
from PyQt6.QtCore import Qt
from config import RESULT_COL_MAP


class ResultDialog(QDialog):
    def __init__(self, df, parent=None):
        super().__init__(parent)
        self.df = df
        self.setWindowTitle("Evaluation Results")
        self.resize(1100, 500)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        header = QLabel(f"Per-cycle results  —  {len(self.df)} cycles")
        header.setStyleSheet("font-weight: bold; font-size: 13px; color: #4cceac; margin-bottom: 6px;")
        layout.addWidget(header)

        col_map = {k: v for k, v in RESULT_COL_MAP}
        display_cols = [c for c in self.df.columns if c in col_map]
        headers      = [col_map[c] for c in display_cols]

        table = QTableWidget(len(self.df), len(display_cols))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        table.verticalHeader().setDefaultSectionSize(22)
        table.setAlternatingRowColors(True)
        table.setStyleSheet(
            "QTableWidget::item:alternate { background-color: #1a2535; }"
            "font-family: 'Consolas', monospace; font-size: 11px;"
        )

        for row_idx, (_, row) in enumerate(self.df[display_cols].iterrows()):
            for col_idx, col in enumerate(display_cols):
                val = row[col]
                if hasattr(val, '__float__'):
                    try:
                        text = f"{float(val):.5f}"
                    except (ValueError, TypeError):
                        text = str(val)
                else:
                    text = str(val) if val is not None else ""
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                table.setItem(row_idx, col_idx, item)

        layout.addWidget(table)

        btn_row = QHBoxLayout()
        btn_export = QPushButton("Export CSV")
        btn_export.clicked.connect(self._export)
        btn_close  = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_export)
        btn_row.addStretch()
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

    def _export(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Results", "results.csv", "CSV files (*.csv)"
        )
        if path:
            self.df.to_csv(path, sep=";", index=False)
