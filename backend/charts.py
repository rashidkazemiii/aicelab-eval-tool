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
    fig.add_trace(go.Scattergl(
        x=raw_df["Time [s]"], y=raw_df["CoF"],
        mode="lines", name="CoF",
        line=dict(color="#2980b9", width=2),
    ))
    if "Filtered CoF" in raw_df.columns:
        fig.add_trace(go.Scattergl(
            x=raw_df["Time [s]"], y=raw_df["Filtered CoF"],
            mode="lines", name="Filtered CoF",
            line=dict(color="#e67e22", width=1.5),
        ))
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


def build_cof_figure(df_display, df_proc, cof_eval, step_df, filter_active):
    """Build the go.Figure for the CoF Analysis tab's chart. `df_display`
    must not be None - the caller shows its own placeholder for that case.
    """
    fig = go.Figure()

    if filter_active:
        cof_line_color = "rgba(41,128,185,0.35)"
    else:
        cof_line_color = "#2980b9"

    cof_x, cof_y = table_helpers.decimate_min_max(
        df_display["Zeit"], df_display["CoF"], CHART_MAX_POINTS
    )
    fig.add_trace(go.Scattergl(
        x=cof_x, y=cof_y,
        mode="lines", name="CoF",
        line=dict(color=cof_line_color, width=2),
    ))
    if filter_active:
        filtered_x, filtered_y = table_helpers.decimate_min_max(
            df_proc["Zeit"], df_proc["CoF"], CHART_MAX_POINTS
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


def figure_to_zoom_iframe_html(fig):
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
    accessible. __cofXR on the parent window stores the x-axis zoom range
    across cell re-renders (marimo rebuilds this whole figure/iframe on every
    reactive update, so the zoom range has to live outside of it to survive).
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

    iframe_html = f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<style>body{{margin:0;overflow:hidden}}</style>
<script src="{cdn}"></script>
</head><body>
<div id="c" style="width:100vw;height:420px"></div>
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
function scheduleYRefit(xMin, xMax) {{
  if (yRefitTimer) clearTimeout(yRefitTimer);
  yRefitTimer = setTimeout(function() {{
    var newYRange = fitYRange(xMin, xMax);
    if (newYRange) {{ Plotly.relayout("c", {{"yaxis.range": newYRange}}); }}
  }}, 100);
}}

window.onload = function() {{
  var xr; try {{ xr = window.parent.__cofXR; }} catch(e) {{}}
  if (xr) {{ l.xaxis = l.xaxis || {{}}; l.xaxis.range = xr; l.xaxis.autorange = false; }}

  var initialXMin = xr ? xr[0] : null, initialXMax = xr ? xr[1] : null;
  var initialYRange = fitYRange(initialXMin, initialXMax);
  if (initialYRange) {{ l.yaxis = l.yaxis || {{}}; l.yaxis.range = initialYRange; l.yaxis.autorange = false; }}

  Plotly.react("c", d, l, {{ scrollZoom: true, displayModeBar: true, responsive: true }})
    .then(function() {{
      document.getElementById("c").on("plotly_relayout", function(e) {{
        var newXMin = null, newXMax = null;
        if ("xaxis.range[0]" in e) {{
          newXMin = e["xaxis.range[0]"]; newXMax = e["xaxis.range[1]"];
          try {{ window.parent.__cofXR = [newXMin, newXMax]; }} catch(ex) {{}}
        }} else if (e["xaxis.autorange"]) {{
          try {{ window.parent.__cofXR = null; }} catch(ex) {{}}
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
    return f"<iframe srcdoc='{srcdoc}' style='width:100%;height:440px;border:none;display:block'></iframe>"
