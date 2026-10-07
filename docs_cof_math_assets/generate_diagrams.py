"""Regenerates the PNG diagrams used on the Help page (docs_cof_math.html).

Run with: python docs_cof_math_assets/generate_diagrams.py
Requires matplotlib. Output files land next to this script.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path as MplPath
import numpy as np
import os

INK = "#172328"
SOFT = "#55666d"
HI = "#8a4a14"
HI_TINT = "#f2e3d3"
OUTDIR = os.path.dirname(os.path.abspath(__file__))


def new_fig(w, h):
    fig = plt.figure(figsize=(w / 100, h / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w)
    ax.set_ylim(h, 0)  # match SVG's top-left origin
    ax.axis("off")
    return fig, ax


def save(fig, name):
    path = os.path.join(OUTDIR, name)
    fig.savefig(path, transparent=True)
    plt.close(fig)
    print("wrote", path)


def square_wave(x_start, x_end, y_zero, height, peak, n_strokes, noise=0.0, seed=0):
    """Friction-style square wave: each stroke jumps to a short static peak,
    then settles onto a flat plateau, then reverses sign for the next stroke.
    Starts and ends on the zero line. y grows downwards (SVG-style axes)."""
    rng = np.random.default_rng(seed)
    stroke_width = (x_end - x_start) / n_strokes
    xs = [x_start]
    ys = [y_zero]
    sign = 1
    for stroke in range(n_strokes):
        x0 = x_start + stroke * stroke_width
        # Edge and peak widths are fixed in pixels, so long strokes still get sharp edges
        edge = 2
        settle = min(0.09 * stroke_width, 6)
        xs.append(x0 + edge)
        ys.append(y_zero - sign * (height + peak))
        xs.append(x0 + edge + settle)
        ys.append(y_zero - sign * height)
        if noise > 0:
            plateau_x = np.linspace(x0 + edge + settle + 2, x0 + stroke_width - edge, 8)
            for x in plateau_x:
                xs.append(x)
                ys.append(y_zero - sign * height + rng.uniform(-noise, noise))
        else:
            xs.append(x0 + stroke_width - edge)
            ys.append(y_zero - sign * height)
        sign = -sign
    xs.append(x_end)
    ys.append(y_zero)
    return xs, ys


# ---------------------------------------------------------------- diagram 1
def diagram_overview():
    fig, ax = new_fig(900, 230)
    ax.axhline(115, color=SOFT, lw=1)
    for x in (250, 460, 670):
        ax.plot([x, x], [15, 200], color=SOFT, lw=1, linestyle=(0, (3, 4)))

    # (start x, end x, plateau height, peak height, strokes) - more strokes = higher frequency
    steps = [(40, 250, 18, 8, 2), (250, 460, 30, 10, 4), (460, 670, 42, 12, 8), (670, 860, 54, 14, 12)]
    for x_start, x_end, height, peak, n_strokes in steps:
        xs, ys = square_wave(x_start, x_end, 115, height, peak, n_strokes)
        ax.plot(xs, ys, color=INK, lw=1.6)

    ax.text(450, 218, "Time", ha="center", fontsize=11)
    ax.text(14, 115, "CoF", ha="center", va="center", fontsize=11, rotation=90)
    for x, label in [(145, "Step 1"), (355, "Step 2"), (565, "Step 3"), (765, "Step 4")]:
        ax.text(x, 205, label, ha="center", fontsize=10, color=SOFT)
    save(fig, "diagram-overview.png")


# ---------------------------------------------------------------- diagram 2
def diagram_offset_filter():
    fig, ax = new_fig(900, 220)

    ax.plot([30, 420], [170, 170], color=SOFT, lw=1, linestyle=(0, (3, 4)))
    ax.text(16, 174, "0", fontsize=10, color=SOFT)
    ax.plot([40, 190], [120, 120], color=SOFT, lw=1)
    ax.text(115, 152, "mean(μ)", ha="center", fontsize=9, color=SOFT)
    xs, ys = square_wave(40, 190, 120, 12, 6, 4, noise=5, seed=1)
    ax.plot(xs, ys, color=INK, lw=1.2)
    ax.text(115, 76, "before", ha="center", fontsize=11)

    ax.annotate("", xy=(250, 150), xytext=(205, 150),
                arrowprops=dict(arrowstyle="->", color=SOFT, lw=1.4))
    ax.text(226, 138, "− mean(μ)", ha="center", fontsize=9, color=SOFT)

    xs, ys = square_wave(260, 420, 170, 12, 6, 4, noise=5, seed=1)
    ax.plot(xs, ys, color=HI, lw=1.4)
    ax.text(340, 76, "after (Offset)", ha="center", fontsize=11)

    ax.plot([450, 450], [15, 205], color=SOFT, lw=1)

    ax.plot([480, 870], [170, 170], color=SOFT, lw=1, linestyle=(0, (3, 4)))
    xs, ys = square_wave(490, 640, 170, 12, 6, 4, noise=5, seed=1)
    ax.plot(xs, ys, color=INK, lw=1.2)
    ax.text(565, 76, "μ (after Offset)", ha="center", fontsize=11)

    ax.annotate("", xy=(693, 150), xytext=(650, 150),
                arrowprops=dict(arrowstyle="->", color=SOFT, lw=1.4))
    ax.text(671, 138, "filter()", ha="center", fontsize=9, color=SOFT)

    xs, ys = square_wave(705, 860, 170, 12, 6, 4)
    ax.plot(xs, ys, color=HI, lw=1.8)
    ax.text(782, 76, "filtered μ′", ha="center", fontsize=11)

    save(fig, "diagram-offset-filter.png")


# ---------------------------------------------------------------- diagram 3
def diagram_zero_crossing():
    fig, ax = new_fig(600, 260)
    # One pair of axes: vertical mu axis, and the mu = 0 line doubling as the time axis
    ax.annotate("", xy=(80, 20), xytext=(80, 240),
                arrowprops=dict(arrowstyle="->", color=SOFT, lw=1))
    ax.annotate("", xy=(560, 140), xytext=(80, 140),
                arrowprops=dict(arrowstyle="->", color=SOFT, lw=1))
    ax.text(68, 22, "μ", ha="right", va="top", fontsize=12)
    ax.text(72, 140, "0", ha="right", va="center", fontsize=10, color=SOFT)
    ax.text(556, 150, "Time", ha="right", va="top", fontsize=11)

    ax.plot([245, 335], [202, 68], color=INK, lw=1.4)

    # t-minus: point below zero, so its label goes above the axis
    ax.plot([260, 260], [140, 180], color=SOFT, lw=1, linestyle=(0, (3, 4)))
    ax.scatter([260], [180], color=INK, s=30, zorder=5)
    ax.text(258, 134, "t⁻", ha="right", va="bottom", fontsize=11, color=SOFT)
    ax.text(236, 190, "(t⁻, μ⁻)", ha="right", va="center", fontsize=11)

    # t-plus: point above zero, so its label goes below the axis
    ax.plot([320, 320], [90, 140], color=SOFT, lw=1, linestyle=(0, (3, 4)))
    ax.scatter([320], [90], color=INK, s=30, zorder=5)
    ax.text(322, 146, "t⁺", ha="left", va="top", fontsize=11, color=SOFT)
    ax.text(344, 85, "(t⁺, μ⁺)", ha="left", va="center", fontsize=11)

    # crossing point
    ax.scatter([287], [140], color=HI, s=50, zorder=6)
    ax.text(292, 146, "t$_j$", ha="left", va="top", fontsize=12, color=HI)

    save(fig, "diagram-zero-crossing.png")


# ---------------------------------------------------------------- diagram 4
def diagram_pause_cycle():
    fig, ax = new_fig(820, 200)
    ax.axhline(110, color=SOFT, lw=1)
    for x in (80, 180, 280, 380, 620, 720):
        ax.plot([x, x], [103, 117], color=SOFT, lw=1.4)
    for x, j in [(80, "j=0"), (180, "j=1"), (280, "j=2"), (380, "j=3"), (620, "j=4"), (720, "j=5")]:
        ax.text(x, 133, j, ha="center", fontsize=10, color=SOFT)

    def arc(x1, x2, y_ctrl, label):
        xm = (x1 + x2) / 2
        verts = [(x1, 110), (xm, y_ctrl), (x2, 110)]
        codes = [MplPath.MOVETO, MplPath.CURVE3, MplPath.CURVE3]
        patch = patches.PathPatch(MplPath(verts, codes), facecolor="none", edgecolor=HI, lw=1.6)
        ax.add_patch(patch)
        ax.text(xm, y_ctrl - 8, label, ha="center", fontsize=11, color=HI)

    arc(80, 180, 70, "k=1")
    arc(180, 280, 70, "k=2")
    arc(280, 380, 70, "k=3")
    arc(620, 720, 70, "k=5")

    verts = [(380, 110), (500, 165), (620, 110)]
    codes = [MplPath.MOVETO, MplPath.CURVE3, MplPath.CURVE3]
    patch = patches.PathPatch(MplPath(verts, codes), facecolor="none", edgecolor=SOFT, lw=1.4, linestyle=(0, (4, 4)))
    ax.add_patch(patch)
    ax.text(500, 183, "pause — gap > τ$_{pause}$(s), no cycle k=4", ha="center", fontsize=10, color=SOFT)

    save(fig, "diagram-pause-cycle.png")


# ---------------------------------------------------------------- diagram 5
def diagram_static_dynamic():
    fig, ax = new_fig(820, 290)

    ax.add_patch(patches.Rectangle((60, 20), 70, 175, facecolor=HI_TINT, edgecolor="none"))
    ax.add_patch(patches.Rectangle((200, 20), 420, 175, facecolor="none", edgecolor=SOFT, lw=1, linestyle=(0, (3, 4))))

    ax.plot([60, 760], [195, 195], color=SOFT, lw=1)

    def y_of_t(t):
        if t < 0.1:
            return 180 + (30 - 180) * (t / 0.1)
        elif t < 0.85:
            u = (t - 0.1) / 0.75
            return 105 + 15 * np.sin(u * 3 * 2 * np.pi)
        else:
            u = (t - 0.85) / 0.15
            start_y = 105 + 15 * np.sin(1.0 * 3 * 2 * np.pi)
            return start_y + (180 - start_y) * (u ** 1.3)

    t = np.linspace(0, 1, 200)
    xs = 60 + t * 700
    ys = [y_of_t(v) for v in t]
    ax.plot(xs, ys, color=INK, lw=1.8)

    ax.plot([200, 620], [106, 106], color=SOFT, lw=1, linestyle=(0, (2, 3)))
    ax.text(410, 95, "μ̄$_k$ (mean over window)", ha="center", fontsize=11)

    ax.scatter([130], [30], color=HI, s=45, zorder=5)
    ax.text(152, 24, "μ*$_k$", fontsize=11, color=HI)

    ax.text(95, 13, "static window", ha="center", fontsize=10, color=SOFT)
    ax.text(410, 13, "dynamic window", ha="center", fontsize=10, color=SOFT)

    for x in (60, 130, 200, 620, 760):
        ax.plot([x, x], [195, 205], color=SOFT, lw=1)

    ax.text(60, 213, "startIndex[k−1]", fontsize=9.5, ha="left")
    ax.text(758, 213, "startIndex[k]", fontsize=9.5, ha="right")
    ax.text(130, 234, "endIndex", fontsize=9.5, ha="center")
    ax.text(620, 234, "enddynamicIndex", fontsize=9.5, ha="right")
    ax.text(200, 255, "startdynamicIndex", fontsize=9.5, ha="left")

    save(fig, "diagram-static-dynamic.png")


# ---------------------------------------------------------------- diagram 6
def hatch_below(ax, x_start, x_end, y):
    """Ground hatching: a line with short slanted ticks underneath it."""
    ax.plot([x_start, x_end], [y, y], color=SOFT, lw=1.2)
    for x in np.arange(x_start, x_end, 12):
        ax.plot([x, x - 8], [y, y + 8], color=SOFT, lw=0.8)


def force_arrow(ax, x_from, y_from, x_to, y_to, color):
    ax.annotate("", xy=(x_to, y_to), xytext=(x_from, y_from),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=2, mutation_scale=14))


def diagram_device():
    fig, ax = new_fig(900, 330)

    # fixed frame: ground and the two side walls
    hatch_below(ax, 120, 780, 270)
    for x_wall in (140, 760):
        ax.add_patch(patches.Rectangle((x_wall - 10, 170), 20, 100,
                                       facecolor="#d7e0e3", edgecolor=SOFT, lw=1))

    # left and right force sensors, between the walls and the lower part
    for x_sensor in (150, 720):
        ax.add_patch(patches.Rectangle((x_sensor, 195), 30, 50,
                                       facecolor=SOFT, edgecolor=INK, lw=1))
    ax.text(165, 290, "Left sensor (Links)", ha="center", va="top", fontsize=9.5, color=SOFT)
    ax.text(735, 290, "Right sensor (Rechts)", ha="center", va="top", fontsize=9.5, color=SOFT)

    # lower part: fixed (constant)
    ax.add_patch(patches.Rectangle((180, 180), 540, 90,
                                   facecolor="#e8eef0", edgecolor=INK, lw=1.4))
    ax.text(200, 262, "Lower part — fixed", ha="left", va="bottom", fontsize=10.5)

    # upper part: slides back and forth
    ax.add_patch(patches.Rectangle((390, 110), 120, 70,
                                   facecolor="#ffffff", edgecolor=INK, lw=1.4))
    ax.text(450, 145, "Upper part\nslides", ha="center", va="center", fontsize=10)
    ax.annotate("", xy=(330, 145), xytext=(385, 145),
                arrowprops=dict(arrowstyle="->", color=INK, lw=1.4))
    ax.annotate("", xy=(570, 145), xytext=(515, 145),
                arrowprops=dict(arrowstyle="->", color=INK, lw=1.4))
    ax.text(580, 145, "stroke\n(back and forth)", ha="left", va="center", fontsize=9.5, color=SOFT)

    # applied load pressing the upper part down
    force_arrow(ax, 450, 30, 450, 106, INK)
    ax.text(460, 45, "Load (Belastung)", ha="left", va="center", fontsize=10)

    # forces acting on the fixed lower part
    # normal force pressed into it at the contact
    force_arrow(ax, 450, 184, 450, 240, HI)
    ax.text(442, 228, "F$_N$", ha="right", va="center", fontsize=12, color=HI)
    # friction force dragging it along with the sliding part
    force_arrow(ax, 460, 196, 560, 196, HI)
    ax.text(566, 196, "F$_f$", ha="left", va="center", fontsize=12, color=HI)
    # the two sensors hold it still: their forces together balance F_f
    force_arrow(ax, 236, 225, 184, 225, HI)
    ax.text(242, 225, "F$_{f,L}$", ha="left", va="center", fontsize=12, color=HI)
    force_arrow(ax, 716, 225, 664, 225, HI)
    ax.text(658, 225, "F$_{f,R}$", ha="right", va="center", fontsize=12, color=HI)

    save(fig, "diagram-device.png")


# ---------------------------------------------------------------- diagram 7
def diagram_crossings_to_peaks():
    fig, ax = new_fig(900, 280)
    y_zero = 140
    height = 45
    peak = 20
    x_start = 60
    x_end = 860
    n_strokes = 4
    stroke_width = (x_end - x_start) / n_strokes

    ax.annotate("", xy=(880, y_zero), xytext=(40, y_zero),
                arrowprops=dict(arrowstyle="->", color=SOFT, lw=1))
    ax.text(880, y_zero - 8, "Time", ha="right", va="bottom", fontsize=10.5)
    ax.text(34, y_zero, "0", ha="right", va="center", fontsize=10, color=SOFT)

    sign = 1
    for stroke in range(n_strokes):
        x0 = x_start + stroke * stroke_width
        x1 = x0 + stroke_width

        # search window right after the crossing (where the peak is looked for)
        if sign > 0:
            window_top = y_zero - height - peak - 8
        else:
            window_top = y_zero
        ax.add_patch(patches.Rectangle((x0, window_top), 0.1 * stroke_width, height + peak + 8,
                                       facecolor=HI_TINT, edgecolor="none"))

        # stroke bracket underneath / above, labelled with the cycle number
        if sign > 0:
            y_bracket = 222
        else:
            y_bracket = 58
        ax.annotate("", xy=(x0 + 4, y_bracket), xytext=(x1 - 4, y_bracket),
                    arrowprops=dict(arrowstyle="<->", color=SOFT, lw=1))
        if sign > 0:
            ax.text((x0 + x1) / 2, y_bracket + 6, "stroke k=" + str(stroke + 1),
                    ha="center", va="top", fontsize=9.5, color=SOFT)
        else:
            ax.text((x0 + x1) / 2, y_bracket - 6, "stroke k=" + str(stroke + 1),
                    ha="center", va="bottom", fontsize=9.5, color=SOFT)

        # the peak found inside the window
        ax.scatter([x0 + 2], [y_zero - sign * (height + peak)], color=HI, s=40, zorder=6)
        if sign > 0:
            ax.text(x0 + 10, y_zero - height - peak - 4, "peak μ*", ha="left", va="bottom",
                    fontsize=10, color=HI)
        else:
            ax.text(x0 + 10, y_zero + height + peak + 4, "peak μ*", ha="left", va="top",
                    fontsize=10, color=HI)
        sign = -sign

    xs, ys = square_wave(x_start, x_end, y_zero, height, peak, n_strokes)
    ax.plot(xs, ys, color=INK, lw=1.6)

    # zero crossings: they mark where each stroke starts
    for stroke in range(n_strokes + 1):
        x_cross = x_start + stroke * stroke_width
        ax.scatter([x_cross], [y_zero], facecolor="white", edgecolor=INK, s=45, lw=1.5, zorder=7)
        ax.text(x_cross - 4, y_zero + 6, "j=" + str(stroke), ha="right", va="top",
                fontsize=9, color=INK)

    save(fig, "diagram-crossings-peaks.png")


if __name__ == "__main__":
    diagram_overview()
    diagram_offset_filter()
    diagram_zero_crossing()
    diagram_pause_cycle()
    diagram_static_dynamic()
    diagram_device()
    diagram_crossings_to_peaks()
