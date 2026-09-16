"""Builds the Plotly figures for the CoF Analysis and History tabs' charts.

Kept separate from app.py so the figure-building and the iframe/JS glue that
gives the CoF chart persistent x-zoom can be read and edited without wading
through marimo cell mechanics.
"""

import io
import json
import re

import plotly.graph_objects as go

import table_helpers

# Shared marker styling for the 5 evaluation-marker traces that both the
# History tab chart and the CoF Analysis chart draw identically.
COF_MARKER_STYLES = {
    "zero_crossing": dict(symbol="line-ns", size=10, color="#888",
                           line=dict(color="#888", width=1.5)),
    "static":        dict(symbol="circle", size=7, color="#e74c3c",
                           line=dict(color="#c0392b", width=1)),
    "dynamic":       dict(symbol="diamond", size=7, color="#2ecc71",
                           line=dict(color="#27ae60", width=1)),
    "dynamic_start": dict(symbol="triangle-right", size=8, color="#9b59b6",
                           line=dict(color="#8e44ad", width=1)),
    "dynamic_end":   dict(symbol="triangle-left", size=8, color="#1abc9c",
                           line=dict(color="#16a085", width=1)),
}


def add_cof_marker_trace(fig, x, y, kind, name):
    # Scattergl (WebGL), not Scatter (SVG): with a long test file Evaluate
    # can find hundreds of cycles, meaning hundreds of marker points per
    # trace across 5 traces. SVG markers need every point's screen
    # position rewritten as real DOM attributes on each redraw; WebGL
    # markers are a GPU buffer update instead, which is what makes the
    # chart still feel responsive after zooming into a busy evaluation.
    fig.add_trace(go.Scattergl(
        x=x, y=y, mode="markers", name=name,
        marker=dict(COF_MARKER_STYLES[kind]),  # copy so Plotly never mutates the shared dict
    ))


def build_history_figure(raw_df, eval_df):
    """Build the go.Figure for a saved test's History-tab chart, or None if
    `raw_df` has no raw signal saved. `raw_df`/`eval_df` are the same two
    tables the History tab's Results/Evaluation Results tables show - kept
    separate for the same reason as the live CoF Analysis chart: raw_df has
    one row per raw sample, eval_df one row per cycle/step/zero-crossing.
    """
    if raw_df.empty or "Time [s]" not in raw_df.columns:
        return None

    fig = go.Figure()
    # Same reasoning as the live CoF Analysis chart (build_cof_figure below):
    # a saved test can have 100,000+ raw samples, which is both slow to pan/
    # zoom and, rendered through mo.ui.plotly, large enough to trip marimo's
    # own output-size limit - decimate before adding either raw-sample trace.
    # Full resolution is kept around the static CoF points (see
    # decimate_for_chart), so the static peaks look exactly as measured.
    static_times = list(eval_df["Static CoF time [s]"].dropna())
    cof_x, cof_y = decimate_for_chart(raw_df["Time [s]"], raw_df["CoF"], static_times)
    fig.add_trace(go.Scattergl(
        x=cof_x, y=cof_y,
        mode="lines", name="CoF",
        line=dict(color="#2980b9", width=2),
    ))
    if "Filtered CoF" in raw_df.columns:
        filtered_x, filtered_y = decimate_for_chart(
            raw_df["Time [s]"], raw_df["Filtered CoF"], static_times
        )
        fig.add_trace(go.Scattergl(
            x=filtered_x, y=filtered_y,
            mode="lines", name="Filtered CoF",
            line=dict(color="#e67e22", width=1.5),
        ))
    # A y=0 reference line, so it is visible where the curve sits relative
    # to zero (with Offset on, the curve is centred on it).
    fig.add_hline(y=0, line=dict(color="#999", width=1))
    zc = eval_df["Min time [s]"].dropna()
    add_cof_marker_trace(fig, zc, [0] * len(zc), "zero_crossing", "Zero crossings")
    s = eval_df[["Static CoF time [s]", "Static CoF"]].dropna()
    add_cof_marker_trace(fig, s["Static CoF time [s]"], s["Static CoF"], "static", "Static CoF")
    d = eval_df[["Dynamic CoF time [s]", "Dynamic CoF"]].dropna()
    add_cof_marker_trace(fig, d["Dynamic CoF time [s]"], d["Dynamic CoF"], "dynamic", "Dynamic CoF")
    ds = eval_df[["Dynamic start time [s]", "Dynamic start CoF"]].dropna()
    add_cof_marker_trace(fig, ds["Dynamic start time [s]"], ds["Dynamic start CoF"], "dynamic_start", "Dynamic start")
    de = eval_df[["Dynamic end time [s]", "Dynamic end CoF"]].dropna()
    add_cof_marker_trace(fig, de["Dynamic end time [s]"], de["Dynamic end CoF"], "dynamic_end", "Dynamic end")
    fig.update_layout(
        height=420,
        xaxis_title="Time [s]", yaxis_title="CoF [-]",
        margin=dict(l=60, r=20, t=20, b=50),
        plot_bgcolor="#fff", paper_bgcolor="#fff",
        font=dict(color="#1f2a40", size=12),
        dragmode="pan",
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0),
        xaxis=dict(gridcolor="#efefef", linecolor="#ddd"),
        yaxis=dict(autorange=True, fixedrange=True, gridcolor="#efefef", linecolor="#ddd"),
    )
    return fig


# A long test can be 100,000+ raw samples, and a chart only a few hundred
# pixels wide can't show more detail than that anyway - plotting every raw
# point just makes panning/zooming slow with no visual benefit.
# decimate_min_max keeps the curve's shape (spikes included) while capping
# how many points the browser actually has to draw.
CHART_MAX_POINTS = 12000

# Placeholder text of the hidden marimo text field the chart's "Evaluate
# with pulse" button writes into (JSON: the per-step offsets in ms plus a
# click nonce). The iframe's JS finds the field by this placeholder, so
# app.py must create the field with exactly this text.
PULSE_EVAL_PLACEHOLDER = "__pulse_eval_request__"

# Around each static CoF point the raw curve is kept at full resolution
# (every sample within +/- this many seconds), so the static peak is shown
# exactly as measured rather than through the decimation buckets. The total
# number of such full-resolution samples is capped at
# STATIC_WINDOW_MAX_POINTS; with more cycles than fit, the window narrows.
STATIC_WINDOW_HALF_WIDTH_S = 0.1
STATIC_WINDOW_MAX_POINTS = 60000


# Decimal places kept in the chart's line traces. Filtered / offset CoF
# values carry 15 decimals (~18 characters each in the chart's JSON), which
# makes a 70,000-point trace over 1 MB on its own. The raw CoF is already
# rounded to 5 decimals upstream, and 1 kHz time stamps need 3, so this
# loses nothing visible. Display only - the evaluation never sees these.
CHART_TIME_DECIMALS = 4
CHART_COF_DECIMALS = 5


def decimate_for_chart(x, y, static_times):
    """Decimate one raw-sample trace for the chart, keeping full resolution
    around the static CoF times (an empty list means plain decimation), and
    round the kept values to CHART_TIME_DECIMALS / CHART_COF_DECIMALS."""
    out_x, out_y = table_helpers.decimate_keep_windows(
        x, y, CHART_MAX_POINTS,
        static_times, STATIC_WINDOW_HALF_WIDTH_S, STATIC_WINDOW_MAX_POINTS,
    )
    rounded_x = []
    for v in out_x:
        rounded_x.append(round(float(v), CHART_TIME_DECIMALS))
    rounded_y = []
    for v in out_y:
        if v is None or v != v:  # keep NaN gaps as they are
            rounded_y.append(v)
        else:
            rounded_y.append(round(float(v), CHART_COF_DECIMALS))
    return rounded_x, rounded_y


def build_cof_figure(df_display, df_proc, cof_eval, step_df, filter_active, speed_pulse=None):
    """Build the go.Figure for the CoF Analysis tab's chart. `df_display`
    must not be None - the caller shows its own placeholder for that case.
    `speed_pulse` is speed_pulse.build_speed_pulse's result (or None): the
    nominal-speed square wave drawn on top of the CoF for comparison.
    """
    fig = go.Figure()

    if filter_active:
        cof_line_color = "rgba(41,128,185,0.35)"
    else:
        cof_line_color = "#2980b9"

    # Full resolution is kept around the static CoF points (see
    # decimate_for_chart), so the static peaks look exactly as measured.
    # Before Evaluate has run there are no static points yet, so this is
    # plain decimation.
    static_times = []
    if cof_eval is not None:
        static_times = list(cof_eval["cof_res"]["staticCoFTime"])
    cof_x, cof_y = decimate_for_chart(df_display["Zeit"], df_display["CoF"], static_times)
    fig.add_trace(go.Scattergl(
        x=cof_x, y=cof_y,
        mode="lines", name="CoF",
        line=dict(color=cof_line_color, width=2),
    ))
    if filter_active:
        filtered_x, filtered_y = decimate_for_chart(
            df_proc["Zeit"], df_proc["CoF"], static_times
        )
        fig.add_trace(go.Scattergl(
            x=filtered_x, y=filtered_y,
            mode="lines", name="Filtered CoF",
            line=dict(color="#e67e22", width=1.5),
        ))

    # Evaluation markers - always a small number of points (a few hundred at
    # most, one per detected cycle), so decimation is not needed here - only
    # the raw-sample line traces above are big enough to matter.
    if cof_eval is not None:
        mn = cof_eval["minima"]
        cr = cof_eval["cof_res"]
        add_cof_marker_trace(fig, mn["Min Zeit"], [0] * len(mn), "zero_crossing", "Zero crossings")
        add_cof_marker_trace(fig, cr["staticCoFTime"], cr["staticCoF"], "static", "Static CoF")
        add_cof_marker_trace(fig, cr["dynamicCoFTime"], cr["dynamicCoF"], "dynamic", "Dynamic CoF")
        add_cof_marker_trace(fig, cr["startdynamicTime"], cr["startdynamicCoF"], "dynamic_start", "Dynamic start")
        add_cof_marker_trace(fig, cr["enddynamicTime"], cr["enddynamicCoF"], "dynamic_end", "Dynamic end")

    # Nominal-speed square wave: flips sign every 30/Drehzahl seconds, so
    # each vertical edge is where a zero crossing *should* be according to
    # the step table. Plain Scatter (SVG), not Scattergl: it has only a few
    # points per cycle, and the None gaps between steps need SVG's
    # connectgaps=False handling to render as breaks.
    # customdata / meta carry which step each point belongs to and the step
    # list, so the per-step offset boxes in the iframe can shift one step's
    # pulse on its own.
    if speed_pulse is not None:
        fig.add_trace(go.Scatter(
            x=speed_pulse["x"], y=speed_pulse["y"],
            customdata=speed_pulse["point_step"],
            meta=speed_pulse["steps"],
            mode="lines", name="Speed pulse",
            line=dict(color="#7f8c8d", width=1, dash="dot"),
            connectgaps=False,
            hoverinfo="x+y+name",
        ))

    # A y=0 reference line, so it is visible where the curve sits relative
    # to zero (with Offset on, the curve is centred on it).
    fig.add_hline(y=0, line=dict(color="#999", width=1))

    # Step boundary vertical lines
    if step_df is not None:
        for _, r in step_df.iterrows():
            if not r["inactive"]:
                for t in [r["Startzeit [s]"], r["Endzeit [s]"]]:
                    fig.add_vline(x=t, line=dict(color="#ccc", dash="dot", width=1))

    fig.update_layout(
        height=420,
        xaxis_title="Time [s]", yaxis_title="CoF [-]",
        margin=dict(l=60, r=20, t=20, b=50),
        plot_bgcolor="#fff", paper_bgcolor="#fff",
        font=dict(color="#1f2a40", size=12),
        dragmode="pan",
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0),
        xaxis=dict(gridcolor="#efefef", linecolor="#ddd"),
        # autorange=True: always fits all data; fixedrange=True: user cannot zoom y-axis
        yaxis=dict(autorange=True, fixedrange=True, gridcolor="#efefef", linecolor="#ddd"),
    )
    return fig


def figure_to_zoom_iframe_html(fig, zoom_key="default"):
    """Wrap `fig` in a self-contained <iframe> tag with persistent x-zoom.

    The Y-axis is fixedrange (locked against manual drag/scroll) but is NOT
    left on plain autorange, because autorange fits the whole file at once -
    zooming into a narrow time window then leaves the curve looking flat,
    squashed against a Y-scale sized for the entire dataset. The embedded
    fitYRange() JS recomputes a Y range from just the points inside the
    currently-visible X window (skipping inf/-inf/NaN, since a single
    divide-by-near-zero sample elsewhere in the file would otherwise blow out
    the scale) every time the X range changes, so the curve always fills the
    visible plot area.

    srcdoc iframe: scripts execute, same origin as parent so window.parent is
    accessible. window.parent.__cofXR stores each chart's x-axis zoom range
    across cell re-renders (marimo rebuilds this whole figure/iframe on every
    reactive update, so the zoom range has to live outside of it to survive),
    keyed by `zoom_key` since window.parent is shared by every iframe on the
    page - without a distinct key per chart, switching to a different test in
    History (or between History and the live Analysis chart) would apply
    whatever x-range was last zoomed to on an unrelated, differently-scaled
    dataset, leaving the new chart looking blank until Autoscale was clicked.
    Callers must pass a key that changes whenever the underlying dataset does
    (e.g. the test id), so a genuinely different chart starts back at
    autorange instead of inheriting a stale window.
    """
    # CDN URL is pinned to the installed plotly version (avoids version mismatch).
    buf = io.StringIO()
    fig.write_html(buf, include_plotlyjs="cdn", full_html=False)
    m = re.search(r'src="(https://cdn\.plot\.ly/plotly[^"]+\.min\.js)"', buf.getvalue())
    if m:
        cdn = m.group(1)
    else:
        cdn = "https://cdn.plot.ly/plotly-latest.min.js"

    fig_dict = json.loads(fig.to_json())
    data_json = json.dumps(fig_dict["data"])
    layout_json = json.dumps(fig_dict["layout"])
    zoom_key_json = json.dumps(str(zoom_key))
    pulse_eval_placeholder_json = json.dumps(PULSE_EVAL_PLACEHOLDER)

    iframe_html = f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<style>
body{{margin:0;overflow:hidden;font-family:system-ui,sans-serif;background:transparent}}
/* Two separate cards in the iframe - the pulse-offset strip and the plot -
   styled like the page's other cards, with a gap between them. They have
   to share one iframe (typing in a box restyles the plot directly), but
   they should not look like one thing. The pulse card is only shown when
   there is a pulse. Every step gets an identical pill: fixed-width label,
   fixed-width right-aligned number box, so the boxes line up in a row and
   wrap cleanly when there are many steps. */
.card{{background:#fff;border-radius:8px;box-shadow:0 1px 4px rgba(0,0,0,.08)}}
#pulse-card{{display:none;padding:10px 16px 12px 16px;margin-bottom:16px}}
#plot-card{{padding:8px 8px 4px 0}}
#pulse-title{{font-weight:700;font-size:10.5px;letter-spacing:.8px;
  text-transform:uppercase;color:#7a8390;white-space:nowrap;margin-bottom:6px}}
#pulse-row{{display:flex;align-items:center;flex-wrap:wrap;gap:6px 8px;font-size:11.5px;color:#555}}
#pulse-row label{{display:grid;grid-template-columns:132px 62px;align-items:center;gap:6px;
  padding:2px 6px 2px 8px;background:#fff;border:1px solid #dfe3e8;border-radius:5px;white-space:nowrap}}
#pulse-row label span{{color:#444;overflow:hidden;text-overflow:ellipsis}}
#pulse-row label b{{font-weight:600;color:#1f2a40;margin-right:4px}}
#pulse-row input{{width:62px;box-sizing:border-box;font-size:11.5px;text-align:right;font-variant-numeric:tabular-nums;
  padding:2px 5px;border:1px solid #cfd5dc;border-radius:3px;color:#1f2a40;background:#fff}}
#pulse-row input:focus{{outline:none;border-color:#2980b9;box-shadow:0 0 0 2px rgba(41,128,185,.15)}}
#pulse-row button{{height:26px;padding:0 12px;font-size:11.5px;font-weight:600;color:#fff;background:#1f2a40;
  border:1px solid #1f2a40;border-radius:5px;cursor:pointer;white-space:nowrap}}
#pulse-row button:hover{{background:#16202f}}
</style>
<script src="{cdn}"></script>
</head><body>
<div id="pulse-card" class="card">
  <div id="pulse-title">Pulse offset [ms]</div>
  <div id="pulse-row"></div>
</div>
<div id="plot-card" class="card"><div id="c" style="width:100%;height:420px"></div></div>
<script>
var d={data_json}, l={layout_json};

// Plotly.py packs large numeric arrays into a compact typed-array form -
// {{"dtype": "f8", "bdata": "<base64>"}} - instead of a plain JS array, to
// keep the page small. A plain array (small traces) is returned unchanged;
// a packed one is base64-decoded into the matching typed array so normal
// indexing (arr[i], arr.length) works either way.
function decodeTypedArray(spec) {{
  if (Array.isArray(spec)) return spec;
  if (!spec || typeof spec !== "object" || !spec.bdata) return [];
  var binaryString = atob(spec.bdata);
  var bytes = new Uint8Array(binaryString.length);
  for (var i = 0; i < binaryString.length; i++) {{
    bytes[i] = binaryString.charCodeAt(i);
  }}
  var arrayConstructors = {{
    i1: Int8Array, u1: Uint8Array, i2: Int16Array, u2: Uint16Array,
    i4: Int32Array, u4: Uint32Array, f4: Float32Array, f8: Float64Array,
  }};
  var ArrayConstructor = arrayConstructors[spec.dtype];
  if (!ArrayConstructor) return [];
  return new ArrayConstructor(bytes.buffer);
}}

// Decode every trace's x/y ONCE here, up front - not inside fitYRange. A real
// file can be 100,000+ samples, and re-running the base64 decode above on
// every single zoom/pan step (fitYRange used to do exactly that) is what
// caused the chart to lag once there was real data to scroll through.
// Decoding once at load means fitYRange only ever touches plain numbers.
d.forEach(function(trace) {{
  if (trace.x) trace.x = decodeTypedArray(trace.x);
  if (trace.y) trace.y = decodeTypedArray(trace.y);
}});

function fitYRange(xMin, xMax) {{
  var lo = Infinity, hi = -Infinity;
  d.forEach(function(trace) {{
    if (!trace.x || !trace.y) return;
    for (var i = 0; i < trace.y.length; i++) {{
      var x = trace.x[i], y = trace.y[i];
      if (!isFinite(y)) continue;
      if (xMin != null && x < xMin) continue;
      if (xMax != null && x > xMax) continue;
      if (y < lo) lo = y;
      if (y > hi) hi = y;
    }}
  }});
  if (!isFinite(lo) || !isFinite(hi)) return null;
  var pad = (hi - lo) * 0.05 || 0.01;
  return [lo - pad, hi + pad];
}}

// A zoom/pan drag fires many relayout events in a row as the mouse moves.
// Recomputing and re-rendering on every single one of those (the old
// behavior) doubles the redraw work throughout the whole gesture. Waiting
// for a short pause after the last event means the extra redraw happens
// once, right after the user settles on a range, instead of continuously.
var yRefitTimer = null;
var storeY = {{}};
var YKEY = null;
function scheduleYRefit(xMin, xMax) {{
  if (yRefitTimer) clearTimeout(yRefitTimer);
  yRefitTimer = setTimeout(function() {{
    var newYRange = fitYRange(xMin, xMax);
    if (newYRange) {{
      Plotly.relayout("c", {{"yaxis.range": newYRange}});
      try {{ storeY[YKEY] = newYRange; }} catch(ex) {{}}
    }}
  }}, 100);
}}

// The speed-pulse offsets are handled entirely here in the browser: one
// box per step, and typing in a box only restyles the "Speed pulse" trace's
// x values for that step's points (found through customdata), so nothing
// on the marimo page re-runs. The values are parked on window.parent (like
// the zoom range) so they survive the chart being rebuilt, e.g. after
// Evaluate.
function setupPulseOffset() {{
  var pulseIndex = -1;
  for (var i = 0; i < d.length; i++) {{
    if (d[i].name === "Speed pulse") {{ pulseIndex = i; }}
  }}
  var row = document.getElementById("pulse-row");
  var card = document.getElementById("pulse-card");
  if (pulseIndex < 0) {{ card.style.display = "none"; return; }}
  var trace = d[pulseIndex];
  var steps = trace.meta || [];
  var pointStep = decodeTypedArray(trace.customdata || []);
  if (steps.length === 0) {{ card.style.display = "none"; return; }}
  card.style.display = "block";

  var originalX = Array.prototype.slice.call(trace.x);
  var offsets; try {{
    window.parent.__cofPulseOffsetsMs = window.parent.__cofPulseOffsetsMs || {{}};
    offsets = window.parent.__cofPulseOffsetsMs;
  }} catch(e) {{ offsets = {{}}; }}

  function offsetFor(stepIndex) {{
    var ms = Number(offsets[stepIndex]);
    if (!isFinite(ms)) return 0;
    return ms;
  }}
  function shiftedX() {{
    var out = new Array(originalX.length);
    for (var i = 0; i < originalX.length; i++) {{
      if (originalX[i] === null || originalX[i] === undefined) {{ out[i] = null; }}
      else {{ out[i] = originalX[i] + offsetFor(pointStep[i]) / 1000; }}
    }}
    return out;
  }}

  for (var s = 0; s < steps.length; s++) {{
    var label = document.createElement("label");
    var text = document.createElement("span");
    // Label each box with the step's time range instead of its number
    // (plain hyphen: the page string has to stay Latin-1, see ANALYSIS_TAB
    // in app.py).
    var stepName = document.createElement("b");
    stepName.textContent = Math.round(steps[s].start) + "-" + Math.round(steps[s].end) + " s";
    text.appendChild(stepName);
    text.appendChild(document.createTextNode(steps[s].speed + " U/min"));
    var box = document.createElement("input");
    box.type = "number"; box.step = "1";
    box.value = offsetFor(steps[s].index);
    box.dataset.stepIndex = steps[s].index;
    box.addEventListener("input", function(ev) {{
      var ms = Number(ev.target.value);
      if (!isFinite(ms)) return;
      try {{ offsets[ev.target.dataset.stepIndex] = ms; }} catch(e) {{}}
      Plotly.restyle("c", {{ x: [shiftedX()] }}, [pulseIndex]);
    }});
    label.appendChild(text); label.appendChild(box); row.appendChild(label);
  }}
  // "Evaluate with pulse": hands the current offsets to Python by writing
  // them into a hidden marimo text field, using marimo's own
  // "marimo-value-input" event (the same one its widgets use). Python
  // then evaluates with the pulse edges as the zero crossings. The nonce
  // makes every click a new value, so clicking twice with the same
  // offsets still re-evaluates.
  var pulseButton = document.createElement("button");
  pulseButton.type = "button";
  pulseButton.id = "pulse-eval";
  pulseButton.textContent = "Evaluate with pulse";
  pulseButton.addEventListener("click", function() {{
    var request = {{ offsets_ms: offsets, nonce: Date.now() }};
    try {{
      var doc = window.parent.document;
      // Attribute values are JSON-encoded by marimo, so compare against the
      // JSON form; a plain loop avoids any CSS-selector quoting.
      var wanted = JSON.stringify(PULSE_EVAL_PLACEHOLDER);
      var field = null;
      var candidates = doc.querySelectorAll("marimo-text");
      for (var i = 0; i < candidates.length; i++) {{
        if (candidates[i].getAttribute("data-placeholder") === wanted) {{ field = candidates[i]; }}
      }}
      if (!field) return;
      var ev = new window.parent.CustomEvent("marimo-value-input", {{
        bubbles: true, composed: true,
        detail: {{ value: JSON.stringify(request), element: field }},
      }});
      doc.dispatchEvent(ev);
    }} catch(e) {{}}
  }});
  row.appendChild(pulseButton);
  // Apply the saved offsets to the initial data before the first draw.
  trace.x = shiftedX();
}}

var PULSE_EVAL_PLACEHOLDER = {pulse_eval_placeholder_json};

window.onload = function() {{
  var ZOOM_KEY = {zoom_key_json};
  var store; try {{ window.parent.__cofXR = window.parent.__cofXR || {{}}; store = window.parent.__cofXR; }} catch(e) {{ store = {{}}; }}
  // The y-range is remembered the same way (window.parent.__cofYR). On a
  // rebuild of the same chart it is reused instead of being fitted again,
  // so a change that moves the whole curve - the Offset toggle - is seen as
  // the curve moving, not as the axis numbers quietly changing under a
  // curve that stays put. Zooming/panning still refits y (and updates the
  // stored range); Autoscale refits to the whole file.
  try {{ window.parent.__cofYR = window.parent.__cofYR || {{}}; storeY = window.parent.__cofYR; }} catch(e) {{ storeY = {{}}; }}
  YKEY = ZOOM_KEY;
  setupPulseOffset();

  var xr = store[ZOOM_KEY];
  if (xr) {{ l.xaxis = l.xaxis || {{}}; l.xaxis.range = xr; l.xaxis.autorange = false; }}

  var initialXMin = xr ? xr[0] : null, initialXMax = xr ? xr[1] : null;
  var initialYRange = storeY[ZOOM_KEY];
  if (!initialYRange) {{
    initialYRange = fitYRange(initialXMin, initialXMax);
    try {{ storeY[ZOOM_KEY] = initialYRange; }} catch(e) {{}}
  }}
  if (initialYRange) {{ l.yaxis = l.yaxis || {{}}; l.yaxis.range = initialYRange; l.yaxis.autorange = false; }}

  // The strip's height depends on how many steps the file has, so the
  // iframe is sized from the inside once everything is laid out (same
  // origin, so window.frameElement is reachable).
  function fitIframeHeight() {{
    try {{
      var h = document.body.scrollHeight;
      if (window.frameElement && h > 0) {{ window.frameElement.style.height = (h + 4) + "px"; }}
    }} catch(e) {{}}
  }}
  fitIframeHeight();

  Plotly.react("c", d, l, {{ scrollZoom: true, displayModeBar: true, responsive: true }})
    .then(function() {{
      fitIframeHeight();
      document.getElementById("c").on("plotly_relayout", function(e) {{
        var newXMin = null, newXMax = null;
        if ("xaxis.range[0]" in e) {{
          newXMin = e["xaxis.range[0]"]; newXMax = e["xaxis.range[1]"];
          try {{ store[ZOOM_KEY] = [newXMin, newXMax]; }} catch(ex) {{}}
        }} else if (e["xaxis.autorange"]) {{
          try {{ store[ZOOM_KEY] = null; }} catch(ex) {{}}
        }} else {{
          return;  // relayout event unrelated to the x-axis range (e.g. legend click)
        }}
        scheduleYRefit(newXMin, newXMax);
      }});
    }});
}};
</script>
</body></html>"""

    srcdoc = iframe_html.replace("&", "&amp;").replace("<", "&lt;").replace("'", "&#39;")
    # The height is a starting value only; the iframe resizes itself to its
    # content once loaded (fitIframeHeight above).
    return f"<iframe srcdoc='{srcdoc}' style='width:100%;height:440px;border:none;display:block'></iframe>"
