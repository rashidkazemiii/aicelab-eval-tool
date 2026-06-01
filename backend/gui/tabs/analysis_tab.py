import os
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QMessageBox, QSizePolicy,
)
from PyQt6.QtCore import QThreadPool

from gui.state import app_state
from gui.workers import (
    CoFOffsetWorker, CoFFilterWorker, CoFEvaluateWorker,
    StrokeOffsetWorker, StrokeFilterWorker, StrokeEvaluateWorker,
    SaveWorker,
)
from gui.widgets.param_panel import ParamPanel
from gui.widgets.chart_canvas import ChartWidget
from gui.dialogs.result_dialog import ResultDialog

# Series colors (matching web frontend)
_COF_LINE     = "#1e88e5"
_COF_SHIFTED  = "#29b6f6"
_COF_FILTERED = "#e53935"
_STATIC_SCAT  = "#e91e63"
_DYN_SCAT     = "#ff9800"
_DYN_START    = "#4caf50"
_DYN_END      = "#9c27b0"

_STROKE_LINE     = "#ff9800"
_STROKE_SHIFTED  = "#ab47bc"
_STROKE_FILTERED = "#26c6da"


class AnalysisTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        app_state.file_loaded.connect(self._on_file_loaded)
        app_state.evaluated.connect(self._panel.on_evaluated)

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Left: param panel
        self._panel = ParamPanel(self)
        root.addWidget(self._panel)

        # Right: charts
        chart_area = QWidget()
        chart_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        chart_layout = QVBoxLayout(chart_area)
        chart_layout.setContentsMargins(4, 4, 4, 4)
        chart_layout.setSpacing(4)

        self._cof_chart  = ChartWidget("CoF", chart_area)
        self._disp_chart = ChartWidget("Displacement (mm)", chart_area)
        chart_layout.addWidget(self._cof_chart,  stretch=55)
        chart_layout.addWidget(self._disp_chart, stretch=45)

        root.addWidget(chart_area)

        # Connect buttons
        self._panel.btn_cof_offset.clicked.connect(self._cof_offset)
        self._panel.btn_cof_filter.clicked.connect(self._cof_filter)
        self._panel.btn_cof_evaluate.clicked.connect(self._cof_evaluate)
        self._panel.btn_disp_offset.clicked.connect(self._stroke_offset)
        self._panel.btn_disp_filter.clicked.connect(self._stroke_filter)
        self._panel.btn_disp_evaluate.clicked.connect(self._stroke_evaluate)
        self._panel.btn_disp_generate.clicked.connect(self._stroke_evaluate)
        self._panel.btn_results.clicked.connect(self._view_results)
        self._panel.btn_save.clicked.connect(self._save)

    # ------------------------------------------------------------------
    # File loaded
    # ------------------------------------------------------------------

    def _on_file_loaded(self):
        s = app_state.session
        fname = os.path.basename(s.file_path) if s.file_path else ""
        has_stroke = "stroke" in (s.df_work.columns if s.df_work is not None else [])
        self._panel.on_file_loaded(fname, has_stroke)

        # Draw raw CoF
        self._cof_chart.canvas.clear()
        if s.df_work is not None and "cof" in s.df_work.columns:
            self._cof_chart.canvas.plot_series(
                s.df_work["time"], s.df_work["cof"],
                _COF_LINE, "CoF",
            )

        # Draw raw stroke
        self._disp_chart.canvas.clear()
        if s.df_work is not None and "stroke" in s.df_work.columns:
            self._disp_chart.canvas.plot_series(
                s.df_work["time"], s.df_work["stroke"],
                _STROKE_LINE, "Stroke",
            )

    # ------------------------------------------------------------------
    # CoF actions
    # ------------------------------------------------------------------

    def _run_worker(self, worker):
        QThreadPool.globalInstance().start(worker)

    def _cof_offset(self):
        self._panel.btn_cof_offset.setEnabled(False)
        w = CoFOffsetWorker()
        w.signals.finished.connect(self._on_cof_offset_done)
        w.signals.error.connect(self._on_error)
        self._run_worker(w)

    def _on_cof_offset_done(self):
        s = app_state.session
        self._cof_chart.canvas.clear()
        self._cof_chart.canvas.plot_series(
            s.df_work["time"], s.df_work["cof"],
            _COF_LINE, "CoF", alpha=0.4,
        )
        self._cof_chart.canvas.plot_series(
            s.df_work["time"], s.df_work["cof_shifted"],
            _COF_SHIFTED, "CoF offset",
        )
        self._panel.btn_cof_offset.setEnabled(True)
        self._panel.on_cof_offset_done()

    def _cof_filter(self):
        self._panel.btn_cof_filter.setEnabled(False)
        w = CoFFilterWorker(self._panel.filter_window)
        w.signals.finished.connect(self._on_cof_filter_done)
        w.signals.error.connect(self._on_error)
        self._run_worker(w)

    def _on_cof_filter_done(self):
        s = app_state.session
        self._cof_chart.canvas.clear()
        if "cof_shifted" in s.df_work.columns:
            self._cof_chart.canvas.plot_series(
                s.df_work["time"], s.df_work["cof_shifted"],
                _COF_SHIFTED, "CoF offset", alpha=0.4,
            )
        self._cof_chart.canvas.plot_series(
            s.df_work["time"], s.df_work["cof_filtered"],
            _COF_FILTERED, "CoF filtered",
        )
        self._panel.btn_cof_filter.setEnabled(True)
        self._panel.on_cof_filter_done()

    def _cof_evaluate(self):
        self._panel.btn_cof_evaluate.setEnabled(False)
        w = CoFEvaluateWorker(
            self._panel.static_range,
            self._panel.dyn_min,
            self._panel.dyn_max,
        )
        w.signals.finished.connect(self._on_cof_evaluate_done)
        w.signals.error.connect(self._on_error)
        self._run_worker(w)

    def _on_cof_evaluate_done(self):
        s  = app_state.session
        df = s.df_work
        r  = s.df_result

        # Redraw CoF chart with scatter overlays
        self._cof_chart.canvas.clear()
        cof_col = "cof_filtered" if "cof_filtered" in df.columns else (
                  "cof_shifted" if "cof_shifted" in df.columns else "cof")
        self._cof_chart.canvas.plot_series(df["time"], df[cof_col], _COF_FILTERED, cof_col)

        if r is not None and not r.empty:
            static_mask  = r["staticCoFTime"].notna()
            dynamic_mask = r["dynamicCoFTime"].notna()
            start_mask   = r["startdynamicTime"].notna()
            end_mask     = r["enddynamicTime"].notna()

            if static_mask.any():
                self._cof_chart.canvas.plot_scatter(
                    r.loc[static_mask, "staticCoFTime"],
                    r.loc[static_mask, "staticCoF"],
                    _STATIC_SCAT, "Static CoF", marker="^",
                )
            if dynamic_mask.any():
                self._cof_chart.canvas.plot_scatter(
                    r.loc[dynamic_mask, "dynamicCoFTime"],
                    r.loc[dynamic_mask, "dynamicCoF"],
                    _DYN_SCAT, "Dynamic CoF",
                )
            if start_mask.any():
                self._cof_chart.canvas.plot_scatter(
                    r.loc[start_mask, "startdynamicTime"],
                    r.loc[start_mask, "startdynamicCoF"],
                    _DYN_START, "Dyn start", marker="|", size=30,
                )
            if end_mask.any():
                self._cof_chart.canvas.plot_scatter(
                    r.loc[end_mask, "enddynamicTime"],
                    r.loc[end_mask, "enddynamicCoF"],
                    _DYN_END, "Dyn end", marker="|", size=30,
                )

            # Displacement scatter
            dmx_mask = r["dispMaxTime"].notna()
            if dmx_mask.any() and "stroke" in df.columns:
                stroke_col = ("stroke_filtered" if "stroke_filtered" in df.columns
                              else "stroke_shifted" if "stroke_shifted" in df.columns
                              else "stroke")
                self._disp_chart.canvas.clear()
                self._disp_chart.canvas.plot_series(
                    df["time"], df[stroke_col], _STROKE_FILTERED, stroke_col,
                )
                self._disp_chart.canvas.plot_scatter(
                    r.loc[dmx_mask, "dispMaxTime"],
                    r.loc[dmx_mask, "dispMax"],
                    _DYN_SCAT, "Disp max", marker="o",
                )

        self._panel.btn_cof_evaluate.setEnabled(True)
        app_state.evaluated.emit()

    # ------------------------------------------------------------------
    # Displacement actions
    # ------------------------------------------------------------------

    def _stroke_offset(self):
        self._panel.btn_disp_offset.setEnabled(False)
        w = StrokeOffsetWorker()
        w.signals.finished.connect(self._on_stroke_offset_done)
        w.signals.error.connect(self._on_error)
        self._run_worker(w)

    def _on_stroke_offset_done(self):
        s = app_state.session
        self._disp_chart.canvas.clear()
        if "stroke" in s.df_work.columns:
            self._disp_chart.canvas.plot_series(
                s.df_work["time"], s.df_work["stroke"],
                _STROKE_LINE, "Stroke", alpha=0.4,
            )
        self._disp_chart.canvas.plot_series(
            s.df_work["time"], s.df_work["stroke_shifted"],
            _STROKE_SHIFTED, "Stroke offset",
        )
        self._panel.btn_disp_offset.setEnabled(True)
        self._panel.on_stroke_offset_done()

    def _stroke_filter(self):
        self._panel.btn_disp_filter.setEnabled(False)
        w = StrokeFilterWorker(self._panel.filter_window)
        w.signals.finished.connect(self._on_stroke_filter_done)
        w.signals.error.connect(self._on_error)
        self._run_worker(w)

    def _on_stroke_filter_done(self):
        s = app_state.session
        self._disp_chart.canvas.clear()
        if "stroke_shifted" in s.df_work.columns:
            self._disp_chart.canvas.plot_series(
                s.df_work["time"], s.df_work["stroke_shifted"],
                _STROKE_SHIFTED, "Stroke offset", alpha=0.4,
            )
        self._disp_chart.canvas.plot_series(
            s.df_work["time"], s.df_work["stroke_filtered"],
            _STROKE_FILTERED, "Stroke filtered",
        )
        self._panel.btn_disp_filter.setEnabled(True)
        self._panel.on_stroke_filter_done()

    def _stroke_evaluate(self):
        self._panel.btn_disp_evaluate.setEnabled(False)
        w = StrokeEvaluateWorker()
        w.signals.finished.connect(lambda: self._panel.btn_disp_evaluate.setEnabled(True))
        w.signals.error.connect(self._on_error)
        self._run_worker(w)

    # ------------------------------------------------------------------
    # View Results / Save
    # ------------------------------------------------------------------

    def _view_results(self):
        s = app_state.session
        if s.df_result is None or s.df_result.empty:
            return
        dlg = ResultDialog(s.df_result, self)
        dlg.exec()

    def _save(self):
        self._panel.set_save_status("Saving…", "#718096")
        self._panel.btn_save.setEnabled(False)
        w = SaveWorker(force=False)
        w.signals.finished.connect(self._on_saved)
        w.signals.error.connect(self._on_save_error)
        w.signals.conflict.connect(self._on_save_conflict)
        self._run_worker(w)

    def _on_saved(self):
        self._panel.set_save_status("Saved ✓", "#4cceac")
        self._panel.btn_save.setEnabled(True)

    def _on_save_error(self, msg: str):
        short = msg.strip().split("\n")[-1]
        self._panel.set_save_status(f"Error: {short}", "#e53935")
        self._panel.btn_save.setEnabled(True)

    def _on_save_conflict(self, fname: str, date: str):
        self._panel.btn_save.setEnabled(True)
        reply = QMessageBox.question(
            self,
            "File already saved",
            f"'{fname}' was already saved on {date}.\nOverwrite it?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._panel.set_save_status("Saving…", "#718096")
            self._panel.btn_save.setEnabled(False)
            w = SaveWorker(force=True)
            w.signals.finished.connect(self._on_saved)
            w.signals.error.connect(self._on_save_error)
            QThreadPool.globalInstance().start(w)
        else:
            self._panel.set_save_status("", "")

    def _on_error(self, msg: str):
        short = msg.strip().split("\n")[-1]
        QMessageBox.critical(self, "Error", short)
        # Re-enable all buttons on error
        self._panel.btn_cof_offset.setEnabled(True)
        self._panel.btn_cof_filter.setEnabled(
            "cof_shifted" in (app_state.session.df_work.columns
                               if app_state.session.df_work is not None else [])
        )
        self._panel.btn_cof_evaluate.setEnabled(
            "cof_shifted" in (app_state.session.df_work.columns
                               if app_state.session.df_work is not None else [])
        )
        self._panel.btn_disp_offset.setEnabled(True)
        self._panel.btn_disp_filter.setEnabled(False)
        self._panel.btn_disp_evaluate.setEnabled(False)
