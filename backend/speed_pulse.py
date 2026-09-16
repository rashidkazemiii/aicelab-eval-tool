"""A square wave ("speed pulse") built from each step's nominal speed, drawn
on the chart next to the zero crossings found in the CoF signal.

Every test step has a Drehzahl (rev/min). One revolution is one full stroke
(out and back), so the CoF should change sign every half revolution:

    half_period [s] = 60 / Drehzahl / 2 = 30 / Drehzahl

The pulse flips sign at exactly that spacing. Its phase is not in the step
table (the step clock does not start on a stroke reversal), so within each
step the pulse is anchored on the first zero crossing the evaluation found
there; from that edge on it runs at the nominal frequency, so where its
later edges land relative to the detected crossings shows how far the real
motion drifts from the nominal frequency along the step. Before any
crossings exist the pulse simply starts at the step's Startzeit. A manual
offset box in the chart can shift the whole pulse on top of that - that is
done in the browser, not here.

Used for display and comparison only - nothing here feeds the CoF numbers.
"""

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# The pulse is drawn at this fraction of the biggest |CoF| on the chart.
PULSE_AMPLITUDE_FRACTION = 0.5
# A step whose pulse would need more edges than this is skipped: it can only
# happen with a mis-read speed or step length, and the points would make the
# chart too big for the page.
PULSE_MAX_EDGES_PER_STEP = 20000


def build_speed_pulse(df_display, step_df, minima=None):
    """Build the pulse for every active step that has a speed.

    `df_display` is used only to scale the pulse height to the chart.
    `minima` (Find_minima's result, or None before Evaluate has run) gives
    the anchor: each step's pulse is placed so one edge sits on the first
    detected zero crossing in that step, with the pulse going the same way
    the CoF went there. Without crossings the step's Startzeit is used.
    (Shifting the pulse by hand is done in the chart itself, in the browser,
    so it never re-runs anything here.)
    Returns None when there is nothing to build (no steps or no Drehzahl
    column). Otherwise a dict with:
      "x", "y"      - the pulse as a line (None entries break the line
                      between steps so pauses are not joined up),
      "point_step"  - for every x/y point, the 0-based step_df row it
                      belongs to (None on the gap entries) - lets the chart
                      shift one step's pulse without touching the others,
      "steps"       - list of {"index": 0-based step_df row, "speed": U/min,
                      "start": Startzeit [s], "end": Endzeit [s]} for every
                      step that got a pulse, in order,
      "edges"       - DataFrame, one row per pulse edge: step (0-based row
                      in step_df), speed, time [s], and the level after it.
    """
    if step_df is None:
        return None
    if "Drehzahl" not in step_df.columns:
        return None

    amplitude = float(df_display["CoF"].abs().max()) * PULSE_AMPLITUDE_FRACTION
    if amplitude <= 0:
        amplitude = 1.0

    have_crossings = minima is not None and len(minima) > 0
    if have_crossings:
        crossing_times = np.asarray(minima["Min Zeit"], dtype=float)
        neg_times = np.asarray(minima["-Min Zeit"], dtype=float)
        pos_times = np.asarray(minima["+Min Zeit"], dtype=float)

    pulse_x = []
    pulse_y = []
    point_step = []
    steps = []
    edge_step = []
    edge_speed = []
    edge_time = []
    edge_level = []

    for step_index in range(len(step_df)):
        row = step_df.iloc[step_index]
        if bool(row["inactive"]):
            continue
        speed = row["Drehzahl"]
        if speed is None or not np.isfinite(speed) or speed <= 0:
            continue
        step_start = float(row["Startzeit [s]"])
        step_end = float(row["Endzeit [s]"])
        half_period = 30.0 / float(speed)

        # Anchor: the first detected crossing inside this step, and which
        # way the CoF went there (negative sample before the positive one =
        # upward). Startzeit, going upward, when there are no crossings yet.
        anchor_time = step_start
        level_after_anchor = amplitude
        if have_crossings:
            in_step = (crossing_times >= step_start) & (crossing_times <= step_end)
            in_step_positions = np.flatnonzero(in_step)
            if len(in_step_positions) > 0:
                first = in_step_positions[0]
                anchor_time = crossing_times[first]
                if neg_times[first] > pos_times[first]:
                    level_after_anchor = -amplitude

        # Edges at anchor + k * half_period for every k that lands inside the
        # step, including k < 0 for the part of the step before the anchor.
        first_k = int(np.ceil((step_start - anchor_time) / half_period))
        last_k = int(np.floor((step_end - anchor_time) / half_period))
        if last_k - first_k + 1 > PULSE_MAX_EDGES_PER_STEP:
            logger.warning(
                "Speed pulse skipped for step %d: %d edges (Drehzahl %s over %.1f s)",
                step_index + 1, last_k - first_k + 1, speed, step_end - step_start,
            )
            continue

        def level_after_edge(k):
            # Even k has the anchor's level, odd k the opposite one.
            if k % 2 == 0:
                return level_after_anchor
            return -level_after_anchor

        # Level from Startzeit up to the first edge inside the step.
        current_level = level_after_edge(first_k - 1)
        if len(pulse_x) > 0:
            pulse_x.append(None)
            pulse_y.append(None)
            point_step.append(None)
        pulse_x.append(step_start)
        pulse_y.append(current_level)
        point_step.append(step_index)
        for k in range(first_k, last_k + 1):
            t = anchor_time + k * half_period
            new_level = level_after_edge(k)
            pulse_x.append(t)
            pulse_y.append(current_level)
            point_step.append(step_index)
            pulse_x.append(t)
            pulse_y.append(new_level)
            point_step.append(step_index)
            current_level = new_level
            edge_step.append(step_index)
            edge_speed.append(float(speed))
            edge_time.append(t)
            edge_level.append(new_level)
        pulse_x.append(step_end)
        pulse_y.append(current_level)
        point_step.append(step_index)
        steps.append({"index": step_index, "speed": float(speed), "start": step_start, "end": step_end})

    if len(edge_time) == 0:
        return None

    edges = pd.DataFrame({
        "step": edge_step,
        "speed": edge_speed,
        "time": edge_time,
        "level_after": edge_level,
    })
    return {"x": pulse_x, "y": pulse_y, "point_step": point_step, "steps": steps, "edges": edges}


def shift_edges(edges, offsets_s):
    """Copy of the pulse's `edges` table with every edge of step i moved by
    offsets_s[i] seconds (positive = later). Steps not in the dict are left
    where they are. This is what "Evaluate with pulse" uses, so the offsets
    typed in the chart are applied to the cycle boundaries too."""
    shifted = edges.copy()
    if offsets_s is None:
        return shifted
    times = shifted["time"].to_numpy().copy()
    steps = shifted["step"].to_numpy()
    for i in range(len(times)):
        step_index = int(steps[i])
        if step_index in offsets_s:
            times[i] = times[i] + float(offsets_s[step_index])
    shifted["time"] = times
    return shifted
