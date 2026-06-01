DARK_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #141b2d;
    color: #e0e0e0;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 12px;
}
QWidget#sidebar {
    background-color: #1f2a40;
    border-right: 1px solid #2d3748;
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
QPushButton:disabled { background-color: #2d3748; color: #666666; }

QPushButton#nav_btn {
    background-color: transparent;
    color: #a0aec0;
    border-radius: 4px;
    padding: 10px 14px;
    text-align: left;
    font-weight: 500;
}
QPushButton#nav_btn:hover { background-color: #2d3748; color: #e0e0e0; }
QPushButton#nav_btn[active="true"] {
    background-color: #3e4396;
    color: white;
}

QPushButton#btn_save {
    background-color: #2e7d32;
}
QPushButton#btn_save:hover { background-color: #388e3c; }
QPushButton#btn_save:disabled { background-color: #2d3748; color: #666666; }

QPushButton#btn_results {
    background-color: #1a6e5e;
}
QPushButton#btn_results:hover { background-color: #1f8870; }
QPushButton#btn_results:disabled { background-color: #2d3748; color: #666666; }

QPushButton#btn_disp {
    background-color: #5c6bc0;
}
QPushButton#btn_disp:hover { background-color: #6a7ad4; }
QPushButton#btn_disp:disabled { background-color: #2d3748; color: #666666; }

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
    background-color: #1f2a40;
    gridline-color: #2d3748;
    border: none;
    selection-background-color: #3e4396;
}
QTableWidget::item { padding: 4px 8px; }
QHeaderView::section {
    background-color: #141b2d;
    color: #ffffff;
    padding: 6px 8px;
    border: none;
    border-bottom: 2px solid #3e4396;
    font-weight: bold;
}
QTableWidget::item:selected { background-color: #3e4396; }

QSpinBox, QDoubleSpinBox, QLineEdit {
    background-color: #2d3748;
    border: 1px solid #4a5568;
    border-radius: 3px;
    color: #e0e0e0;
    padding: 3px 5px;
}
QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus {
    border: 1px solid #3e4396;
}

QRadioButton { color: #e0e0e0; spacing: 6px; }
QRadioButton::indicator {
    width: 14px; height: 14px;
    border-radius: 7px;
    border: 2px solid #4a5568;
    background-color: #2d3748;
}
QRadioButton::indicator:checked {
    background-color: #4cceac;
    border: 2px solid #4cceac;
}

QScrollBar:vertical {
    background: #1f2a40;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #3e4396;
    border-radius: 4px;
    min-height: 20px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }

QScrollBar:horizontal {
    background: #1f2a40;
    height: 8px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: #3e4396;
    border-radius: 4px;
    min-width: 20px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }

QDialog {
    background-color: #141b2d;
}
QLabel#section_label {
    color: #4cceac;
    font-weight: bold;
    font-size: 11px;
    letter-spacing: 1px;
}
QFrame#separator {
    background-color: #2d3748;
    max-height: 1px;
}
QFrame#drop_area {
    border: 2px dashed #3e4396;
    border-radius: 8px;
    background-color: #1f2a40;
}
QFrame#drop_area:hover {
    border-color: #4cceac;
    background-color: #1a2535;
}
QFrame#file_info {
    background-color: #1f2a40;
    border: 1px solid #2d3748;
    border-radius: 6px;
}
QMessageBox {
    background-color: #141b2d;
    color: #e0e0e0;
}
QMessageBox QPushButton {
    min-width: 70px;
}
"""
