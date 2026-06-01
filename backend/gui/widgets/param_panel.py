from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox,
    QDoubleSpinBox, QPushButton, QFrame, QSizePolicy,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from config import (
    DEFAULT_FILTER_WINDOW, DEFAULT_STATIC_RANGE,
    DEFAULT_DYN_MIN, DEFAULT_DYN_MAX,
)


def _separator():
    line = QFrame()
    line.setObjectName("separator")
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFixedHeight(1)
    return line


def _section_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("section_label")
    lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
    return lbl


class ParamPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(185)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self._build_ui()
        self._set_all_disabled()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 12, 8, 12)
        layout.setSpacing(6)

        # File label
        self.file_label = QLabel("No file loaded")
        self.file_label.setWordWrap(True)
        self.file_label.setStyleSheet("color: #718096; font-size: 10px; font-style: italic;")
        layout.addWidget(self.file_label)
        layout.addWidget(_separator())

        # Parameters
        layout.addWidget(_section_label("PARAMETERS"))
        self.spin_filter = self._spinbox(
            DEFAULT_FILTER_WINDOW, 1, 10000, "Filter points"
        )
        layout.addLayout(self.spin_filter[0])

        self.spin_static = self._dspinbox(
            DEFAULT_STATIC_RANGE, 0.1, 100, "Static CoF (%)"
        )
        layout.addLayout(self.spin_static[0])

        self.spin_dyn_min = self._dspinbox(
            DEFAULT_DYN_MIN, 0.1, 100, "Dynamic Min (%)"
        )
        layout.addLayout(self.spin_dyn_min[0])

        self.spin_dyn_max = self._dspinbox(
            DEFAULT_DYN_MAX, 0.1, 100, "Dynamic Max (%)"
        )
        layout.addLayout(self.spin_dyn_max[0])

        layout.addWidget(_separator())

        # CoF actions
        layout.addWidget(_section_label("COF ACTIONS"))
        self.btn_cof_offset   = self._btn("Offset",   "")
        self.btn_cof_filter   = self._btn("Filter",   "")
        self.btn_cof_evaluate = self._btn("Evaluate", "")
        layout.addWidget(self.btn_cof_offset)
        layout.addWidget(self.btn_cof_filter)
        layout.addWidget(self.btn_cof_evaluate)
        layout.addWidget(_separator())

        # Displacement actions
        layout.addWidget(_section_label("DISPLACEMENT"))
        self.btn_disp_offset   = self._btn("Offset",   "btn_disp")
        self.btn_disp_filter   = self._btn("Filter",   "btn_disp")
        self.btn_disp_evaluate = self._btn("Evaluate", "btn_disp")
        self.btn_disp_generate = self._btn("Generate", "btn_disp")
        layout.addWidget(self.btn_disp_offset)
        layout.addWidget(self.btn_disp_filter)
        layout.addWidget(self.btn_disp_evaluate)
        layout.addWidget(self.btn_disp_generate)
        layout.addWidget(_separator())

        # Results / Save
        self.btn_results = self._btn("View Results", "btn_results")
        layout.addWidget(self.btn_results)

        self.btn_save = self._btn("Save", "btn_save")
        layout.addWidget(self.btn_save)

        self.save_status = QLabel("")
        self.save_status.setStyleSheet("color: #4cceac; font-size: 10px;")
        self.save_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.save_status)

        layout.addStretch()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _btn(self, text: str, obj_name: str = "") -> QPushButton:
        b = QPushButton(text)
        if obj_name:
            b.setObjectName(obj_name)
        b.setFixedHeight(28)
        return b

    def _spinbox(self, default, min_val, max_val, label):
        row = QHBoxLayout()
        row.setSpacing(4)
        lbl = QLabel(label)
        lbl.setStyleSheet("font-size: 10px; color: #a0aec0;")
        sb  = QSpinBox()
        sb.setRange(min_val, max_val)
        sb.setValue(default)
        sb.setFixedHeight(24)
        row.addWidget(lbl, stretch=1)
        row.addWidget(sb, stretch=1)
        return row, sb

    def _dspinbox(self, default, min_val, max_val, label):
        row = QHBoxLayout()
        row.setSpacing(4)
        lbl = QLabel(label)
        lbl.setStyleSheet("font-size: 10px; color: #a0aec0;")
        sb  = QDoubleSpinBox()
        sb.setRange(min_val, max_val)
        sb.setValue(default)
        sb.setDecimals(1)
        sb.setFixedHeight(24)
        row.addWidget(lbl, stretch=1)
        row.addWidget(sb, stretch=1)
        return row, sb

    # ------------------------------------------------------------------
    # State helpers
    # ------------------------------------------------------------------

    def _set_all_disabled(self):
        for btn in (
            self.btn_cof_offset, self.btn_cof_filter, self.btn_cof_evaluate,
            self.btn_disp_offset, self.btn_disp_filter, self.btn_disp_evaluate,
            self.btn_disp_generate, self.btn_results, self.btn_save,
        ):
            btn.setEnabled(False)

    def on_file_loaded(self, file_name: str, has_stroke: bool):
        self.file_label.setText(file_name)
        self.save_status.setText("")
        self.btn_cof_offset.setEnabled(True)
        self.btn_cof_filter.setEnabled(False)
        self.btn_cof_evaluate.setEnabled(False)
        self.btn_disp_offset.setEnabled(has_stroke)
        self.btn_disp_filter.setEnabled(False)
        self.btn_disp_evaluate.setEnabled(False)
        self.btn_disp_generate.setEnabled(False)
        self.btn_results.setEnabled(False)
        self.btn_save.setEnabled(False)

    def on_cof_offset_done(self):
        self.btn_cof_filter.setEnabled(True)
        self.btn_cof_evaluate.setEnabled(True)

    def on_cof_filter_done(self):
        self.btn_cof_evaluate.setEnabled(True)

    def on_evaluated(self):
        self.btn_results.setEnabled(True)
        self.btn_save.setEnabled(True)

    def on_stroke_offset_done(self):
        self.btn_disp_filter.setEnabled(True)
        self.btn_disp_evaluate.setEnabled(True)

    def on_stroke_filter_done(self):
        self.btn_disp_evaluate.setEnabled(True)
        self.btn_disp_generate.setEnabled(True)

    def set_save_status(self, text: str, color: str = "#4cceac"):
        self.save_status.setStyleSheet(f"color: {color}; font-size: 10px;")
        self.save_status.setText(text)

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    @property
    def filter_window(self) -> int:
        return self.spin_filter[1].value()

    @property
    def static_range(self) -> float:
        return self.spin_static[1].value()

    @property
    def dyn_min(self) -> float:
        return self.spin_dyn_min[1].value()

    @property
    def dyn_max(self) -> float:
        return self.spin_dyn_max[1].value()
