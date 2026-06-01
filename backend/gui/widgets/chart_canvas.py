import matplotlib
matplotlib.use("QtAgg")

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from PyQt6.QtWidgets import QWidget, QVBoxLayout

_BG      = "#141b2d"
_AX_BG   = "#1a2238"
_GRID    = "#2d3748"
_TEXT    = "#b0bec5"
_SPINE   = "#3e4396"


class ChartCanvas(FigureCanvasQTAgg):
    def __init__(self, title: str = "", parent=None):
        self._fig = Figure(facecolor=_BG, tight_layout=True)
        super().__init__(self._fig)
        self.setParent(parent)
        self.ax = self._fig.add_subplot(111)
        self._title = title
        self._style_axes()

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

    def clear(self):
        self.ax.cla()
        self._style_axes()
        self.draw()

    def plot_series(self, time_arr, value_arr, color: str, label: str,
                    linewidth: float = 1.2, alpha: float = 1.0):
        self.ax.plot(time_arr, value_arr, color=color, linewidth=linewidth,
                     label=label, alpha=alpha)
        self._update_legend()
        self.draw()

    def plot_scatter(self, time_arr, value_arr, color: str, label: str,
                     marker: str = "o", size: int = 18, zorder: int = 5):
        self.ax.scatter(time_arr, value_arr, c=color, label=label,
                        marker=marker, s=size, zorder=zorder)
        self._update_legend()
        self.draw()

    def _update_legend(self):
        handles, labels = self.ax.get_legend_handles_labels()
        if handles:
            legend = self.ax.legend(
                handles, labels,
                loc="upper right",
                fontsize=7,
                framealpha=0.4,
                facecolor=_BG,
                labelcolor=_TEXT,
            )


class ChartWidget(QWidget):
    """ChartCanvas + NavigationToolbar packaged as a regular QWidget."""

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.canvas  = ChartCanvas(title, self)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        self.toolbar.setStyleSheet(
            "background-color: #1f2a40; color: #e0e0e0; border: none;"
        )
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
