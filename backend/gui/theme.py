DARK_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #f0f2f8;
    color: #2d3748;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 12px;
}
QWidget#sidebar {
    background-color: #ffffff;
    border-right: 1px solid #d1d9e6;
}
QPushButton {
    background-color: #3e4396;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 5px 10px;
    font-weight: 600;
}
QPushButton:hover { background-color: #4d52b0; }
QPushButton:pressed { background-color: #323880; }
QPushButton:disabled { background-color: #c8cfe0; color: #a0aec0; }

QPushButton#nav_btn {
    background-color: transparent;
    color: #718096;
    border-radius: 4px;
    padding: 10px 14px;
    text-align: left;
    font-weight: 500;
}
QPushButton#nav_btn:hover { background-color: #edf0fb; color: #2d3748; }
QPushButton#nav_btn[active="true"] {
    background-color: #3e4396;
    color: white;
}

QPushButton#btn_save {
    background-color: #2e7d32;
}
QPushButton#btn_save:hover { background-color: #388e3c; }
QPushButton#btn_save:disabled { background-color: #c8cfe0; color: #a0aec0; }

QPushButton#btn_results {
    background-color: #00796b;
}
QPushButton#btn_results:hover { background-color: #00897b; }
QPushButton#btn_results:disabled { background-color: #c8cfe0; color: #a0aec0; }

QPushButton#btn_disp {
    background-color: #5c6bc0;
}
QPushButton#btn_disp:hover { background-color: #6a7ad4; }
QPushButton#btn_disp:disabled { background-color: #c8cfe0; color: #a0aec0; }

QPushButton#btn_delete {
    background-color: #c62828;
    padding: 3px 8px;
    font-size: 11px;
}
QPushButton#btn_delete:hover { background-color: #e53935; }

QPushButton#btn_view {
    background-color: #1565c0;
    padding: 3px 8px;
    font-size: 11px;
}
QPushButton#btn_view:hover { background-color: #1976d2; }

QTableWidget {
    background-color: #ffffff;
    gridline-color: #e2e8f0;
    border: 1px solid #d1d9e6;
    selection-background-color: #c5cae9;
    color: #2d3748;
}
QTableWidget::item { padding: 4px 8px; }
QTableWidget::item:alternate { background-color: #f7f9fc; }
QHeaderView::section {
    background-color: #edf2f7;
    color: #2d3748;
    padding: 6px 8px;
    border: none;
    border-bottom: 2px solid #3e4396;
    font-weight: bold;
}
QTableWidget::item:selected { background-color: #c5cae9; color: #1a202c; }

QSpinBox, QDoubleSpinBox, QLineEdit {
    background-color: #ffffff;
    border: 1px solid #cbd5e0;
    border-radius: 3px;
    color: #2d3748;
    padding: 3px 5px;
}
QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus {
    border: 1px solid #3e4396;
}

QRadioButton { color: #2d3748; spacing: 6px; }
QRadioButton::indicator {
    width: 14px; height: 14px;
    border-radius: 7px;
    border: 2px solid #cbd5e0;
    background-color: #ffffff;
}
QRadioButton::indicator:checked {
    background-color: #3e4396;
    border: 2px solid #3e4396;
}

QScrollBar:vertical {
    background: #edf2f7;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #a0aec0;
    border-radius: 4px;
    min-height: 20px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }

QScrollBar:horizontal {
    background: #edf2f7;
    height: 8px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: #a0aec0;
    border-radius: 4px;
    min-width: 20px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }

QDialog {
    background-color: #f0f2f8;
}
QLabel#section_label {
    color: #3e4396;
    font-weight: bold;
    font-size: 11px;
    letter-spacing: 1px;
}
QFrame#separator {
    background-color: #d1d9e6;
    max-height: 1px;
}
QFrame#drop_area {
    border: 2px dashed #3e4396;
    border-radius: 8px;
    background-color: #edf0fb;
}
QFrame#drop_area:hover {
    border-color: #2b9277;
    background-color: #e8f5f1;
}
QFrame#file_info {
    background-color: #edf0fb;
    border: 1px solid #c5cae9;
    border-radius: 6px;
}
QMessageBox {
    background-color: #f0f2f8;
    color: #2d3748;
}
QMessageBox QPushButton {
    min-width: 70px;
}
"""
