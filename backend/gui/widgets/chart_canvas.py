import matplotlib
matplotlib.use("QtAgg")

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.transforms import blended_transform_factory
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt

_BG    = "#141b2d"
_AX_BG = "#1a2238"
_GRID  = "#2d3748"
_TEXT  = "#b0bec5"
_SPINE = "#3e4396"

_ZOOM_FACTOR = 1.20   # 20% zoom per scroll tick


class ChartCanvas(FigureCanvasQTAgg):
    def __init__(self, title: str = "", parent=None):
        self._fig = Figure(facecolor=_BG, tight_layout=True)
        super().__init__(self._fig)
        self.setParent(parent)
        self.ax = self._fig.add_subplot(111)
        self._title = title
        self._style_axes()

        # Pan state
        self._pan_start_px  = None
        self._xlim_at_press = None

        # Full data limits — Y is always locked to these
        self._full_xlim = None
        self._full_ylim = None

        # Connect mouse events
        self._fig.canvas.mpl_connect("scroll_event",        self._on_scroll)
        self._fig.canvas.mpl_connect("button_press_event",  self._on_press)
        self._fig.canvas.mpl_connect("button_release_event",self._on_release)
        self._fig.canvas.mpl_connect("motion_notify_event", self._on_motion)

    # ------------------------------------------------------------------
    # Styling
    # ------------------------------------------------------------------

    def _style_axes(self):
        ax = self.ax
        ax.set_facecolor(_AX_BG)
        ax.tick_params(colors=_TEXT, labelsize=8)
        ax.xaxis.label.set_color(_TEXT)
        ax.yaxis.label.set_color(_TEXT)
        ax.set_xlabel("Time (s)", color=_TEXT, fontsize=9)
        ax.set_ylabel(self._title, color=_TEXT, fontsize=9)
        for spine in ax.spines.values():
            spine.set_edgecolor(_SPINE)
        ax.grid(True, color=_GRID, linewidth=0.5, linestyle="--", alpha=0.6)

    # ------------------------------------------------------------------
    # Public drawing API
    # ------------------------------------------------------------------

    def clear(self):
        self.ax.cla()
        self._full_xlim = None
        self._full_ylim = None
        self._style_axes()
        self.draw()

    def plot_series(self, time_arr, value_arr, color: str, label: str,
                    linewidth: float = 1.2, alpha: float = 1.0):
        self.ax.plot(time_arr, value_arr, color=color, linewidth=linewidth,
                     label=label, alpha=alpha)
        self._update_legend()
        self._save_full_limits()
        self.draw()

    def plot_scatter(self, time_arr, value_arr, color: str, label: str,
                     marker: str = "o", size: int = 18, zorder: int = 5):
        self.ax.scatter(time_arr, value_arr, c=color, label=label,
                        marker=marker, s=size, zorder=zorder)
        self._update_legend()
        self._save_full_limits()
        self.draw()

    def draw_step_lines(self, step_df):
        """Draw vertical dashed lines at each step boundary.
        Only drawn when there are 2+ active steps (SRV / SRV_FSA)."""
        if step_df is None:
            return
        active = step_df[~step_df["inactive"]]
        if len(active) <= 1:
            return

        # x in data coords, y in axes-fraction coords — labels stay at fixed height
        trans = blended_transform_factory(self.ax.transData, self.ax.transAxes)

        for i, (_, row) in enumerate(active.iterrows()):
            t_start = row["step_start"]
            t_end   = row["step_end"]
            label   = f"S{i + 1}" if i < len(active) - 1 else None

            # Step-start line (solid amber)
            self.ax.axvline(t_start, color="#ffa726", linewidth=1.0,
                            linestyle="-", alpha=0.55, zorder=4)
            # Step-end line (dashed, dimmer)
            self.ax.axvline(t_end, color="#ffa726", linewidth=0.8,
                            linestyle="--", alpha=0.35, zorder=4)

            if label:
                self.ax.text(t_start + (t_end - t_start) * 0.02, 0.97,
                             label, transform=trans,
                             color="#ffa726", fontsize=8, alpha=0.85,
                             va="top", ha="left")

        self.draw_idle()

    def reset_zoom(self):
        if self._full_xlim:
            self.ax.set_xlim(self._full_xlim)
        if self._full_ylim:
            self.ax.set_ylim(self._full_ylim)
        self.draw()

    def _save_full_limits(self):
        """Snapshot the auto-scaled limits after each plot call."""
        self.ax.autoscale_view()
        self._full_xlim = self.ax.get_xlim()
        self._full_ylim = self.ax.get_ylim()

    def _update_legend(self):
        handles, labels = self.ax.get_legend_handles_labels()
        if handles:
            self.ax.legend(
                handles, labels,
                loc="upper right",
                fontsize=7,
                framealpha=0.4,
                facecolor=_BG,
                labelcolor=_TEXT,
            )

    # ------------------------------------------------------------------
    # Mouse: scroll = zoom, drag = pan, double-click = reset
    # ------------------------------------------------------------------

    def _on_scroll(self, event):
        if event.inaxes != self.ax or event.xdata is None:
            return
        factor = 1 / _ZOOM_FACTOR if event.button == "up" else _ZOOM_FACTOR
        cx = event.xdata
        xl, xr = self.ax.get_xlim()
        self.ax.set_xlim([cx + (xl - cx) * factor, cx + (xr - cx) * factor])
        self._lock_ylim()
        self.draw_idle()

    def _on_press(self, event):
        if event.inaxes != self.ax:
            return
        if event.dblclick:
            self.reset_zoom()
            return
        if event.button == 1:
            self._pan_start_px  = (event.x, event.y)
            self._xlim_at_press = self.ax.get_xlim()

    def _on_release(self, event):
        self._pan_start_px = None

    def _on_motion(self, event):
        if self._pan_start_px is None or event.inaxes != self.ax:
            return
        inv = self.ax.transData.inverted()
        x0d, _ = inv.transform(self._pan_start_px)
        xcd, _ = inv.transform((event.x, event.y))
        dx = xcd - x0d
        xl, xr = self._xlim_at_press
        self.ax.set_xlim([xl - dx, xr - dx])
        self._lock_ylim()
        self.draw_idle()

    def _lock_ylim(self):
        """Keep Y-axis showing the full data range at all times."""
        if self._full_ylim:
            self.ax.set_ylim(self._full_ylim)


class ChartWidget(QWidget):
    """ChartCanvas with a minimal Reset Zoom button (no heavy toolbar)."""

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Thin top bar with just a reset button and hint label
        bar = QWidget()
        bar.setFixedHeight(24)
        bar.setStyleSheet("background-color: #1a2238;")
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(6, 0, 6, 0)
        bar_layout.setSpacing(8)

        from PyQt6.QtWidgets import QLabel
        hint = QLabel("scroll = zoom  ·  drag = pan  ·  double-click = reset")
        hint.setStyleSheet("color: #4a5568; font-size: 10px;")
        bar_layout.addWidget(hint)
        bar_layout.addStretch()

        btn_reset = QPushButton("⊡ Reset")
        btn_reset.setFixedHeight(20)
        btn_reset.setFixedWidth(60)
        btn_reset.setStyleSheet(
            "background-color: #2d3748; color: #a0aec0; "
            "border: none; border-radius: 3px; font-size: 10px; padding: 0px;"
        )

        bar_layout.addWidget(btn_reset)

        self.canvas = ChartCanvas(title, self)
        btn_reset.clicked.connect(self.canvas.reset_zoom)

        layout.addWidget(bar)
        layout.addWidget(self.canvas)
