import marimo

__generated_with = "0.23.9"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import plotly.graph_objects as go
    import sys, os

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

    from physics import CoF as cof_calc
    from physics import utility_functions
    from physics import statistics as stat_funcs

    return cof_calc, go, mo, stat_funcs, utility_functions




@app.cell
def _(mo):
    mo.Html("""
    <style>
      .navbar {
        background: #1f2a40; padding: 0 24px; height: 50px;
        display: flex; align-items: center; justify-content: space-between;
        border-bottom: 1px solid #2d3748; border-radius: 8px 8px 0 0;
      }
      .navbar-title { color: #4cceac; font-weight: 700; font-size: 1rem; letter-spacing: 0.5px; }
      .navbar-version { color: #fff; font-size: 0.75rem; margin-left: 10px; }
      .navbar-user { color: #aaa; font-size: 0.8rem; }
      .panel { background: #fff; border-radius: 8px; padding: 16px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
      .panel-title { font-weight: 700; color: #1f2a40; font-size: 0.85rem; margin: 0 0 12px 0; }
      .section-label { font-weight: 700; color: #999; font-size: 0.6rem; letter-spacing: 1px; margin: 0 0 6px 0; }
      .divider { border: none; border-top: 1px solid #eee; margin: 10px 0; }
      .upload-wrapper { display: flex; flex-direction: column; align-items: center; padding: 48px 20px; gap: 16px; }
      .upload-title { color: #1f2a40; font-size: 1.05rem; font-weight: 600; margin: 0; }
      table th { padding: 4px 6px !important; min-width: 0 !important; width: auto !important; }
      table td { padding: 4px 6px !important; min-width: 0 !important; width: auto !important; }
      table { table-layout: auto !important; }
      input[type="text"] {
        width: 60px !important;
        max-width: 60px !important;
        min-width: 0 !important;
        box-sizing: border-box !important;
      }
      label:has(input[type="text"]) {
        width: 60px !important;
        max-width: 60px !important;
        min-width: 0 !important;
        overflow: hidden !important;
      }
    </style>
    """)
    return


@app.cell
def _(mo):
    get_eval_params, set_eval_params = mo.state(None)
    return get_eval_params, set_eval_params


@app.cell
def _(mo):
    get_filter_params, set_filter_params = mo.state(None)
    return get_filter_params, set_filter_params


@app.cell
def _(mo):
    get_offset, set_offset = mo.state(False)
    return get_offset, set_offset


@app.cell
def _(mo):
    file_upload = mo.ui.file(label="Upload test file (.txt)", filetypes=[".txt"])
    return (file_upload,)


@app.cell
def _(mo):
    get_parse_params, set_parse_params = mo.state(None)
    return get_parse_params, set_parse_params



@app.cell
def _(get_offset, mo, set_offset):
    nlc           = mo.ui.text(label="", value="")
    offset_btn    = mo.ui.button(
        label="Offset (ON)" if get_offset() else "Offset",
        kind="success" if get_offset() else "neutral",
        on_click=lambda _: set_offset(not get_offset()),
    )
    filter_points = mo.ui.text(label="", value="25")
    static_range  = mo.ui.text(label="", value="10.0")
    dyn_min       = mo.ui.text(label="", value="20.0")
    dyn_max       = mo.ui.text(label="", value="80.0")
    return dyn_max, dyn_min, filter_points, nlc, offset_btn, static_range


@app.cell
def _(file_upload, mo):
    _total = (
        len(file_upload.value[0].contents.decode("latin-1").splitlines())
        if file_upload.value else 0
    )
    start_step_row = mo.ui.text(label="", value="0")
    end_step_row   = mo.ui.text(label="", value="0")
    start_main_row = mo.ui.text(label="", value="41")
    stop_main_row  = mo.ui.text(label="", value=str(_total))
    has_step       = mo.ui.checkbox(label="Has step data", value=True)
    return end_step_row, has_step, start_main_row, start_step_row, stop_main_row


@app.cell
def _(col_step_inactive, col_step_time, col_time, end_step_row, has_step, mo, set_parse_params, start_main_row, start_step_row, stop_main_row):
    calculate_btn = mo.ui.button(
        label="Calculate",
        kind="success",
        on_click=lambda _: set_parse_params({
            "start_step":        int(start_step_row.value),
            "end_step":          int(end_step_row.value),
            "start_main":        int(start_main_row.value),
            "stop_main":         int(stop_main_row.value),
            "has_step":          bool(has_step.value),
            "col_time":          int(col_time.value),
            "col_step_time":     int(col_step_time.value),
            "col_step_inactive": int(col_step_inactive.value),
        }),
    )
    return (calculate_btn,)


@app.cell
def _(dyn_max, dyn_min, filter_points, mo, set_eval_params, set_filter_params, static_range):
    filter_btn   = mo.ui.button(
        label="Filter", kind="neutral",
        on_click=lambda _: set_filter_params({"filter_points": int(filter_points.value)}),
    )
    evaluate_btn = mo.ui.button(
        label="Evaluate", kind="success",
        on_click=lambda _: set_eval_params({
            "static_range": float(static_range.value),
            "dyn_min":      float(dyn_min.value),
            "dyn_max":      float(dyn_max.value),
        }),
    )
    return evaluate_btn, filter_btn


@app.cell
def _(file_upload, get_parse_params, mo):
    import io, pandas as pd

    df_raw  = None
    step_df = None
    load_msg = mo.callout(mo.md("Upload a file, set the row numbers, then click **Calculate**."), kind="info")

    _p = get_parse_params()
    if file_upload.value and _p is not None and _p["start_main"] > 0:
        try:
            _raw   = file_upload.value[0].contents.decode("latin-1")
            _lines = _raw.splitlines()

            # ── Main data ────────────────────────────────────────────────────
            _nrows = (_p["stop_main"] - _p["start_main"]
                      if _p["stop_main"] > _p["start_main"] else None)
            df_raw = pd.read_csv(
                io.StringIO(_raw), sep="\t",
                skiprows=_p["start_main"] - 2,
                nrows=_nrows,
                decimal=",", low_memory=False,
            )
            df_raw.columns = df_raw.columns.str.strip()
            df_raw = df_raw.apply(pd.to_numeric, errors="coerce")

            # ── Step data (optional) ─────────────────────────────────────────
            if _p["has_step"] and _p["start_step"] > 0 and _p["end_step"] > _p["start_step"]:
                _step_text = "\n".join(_lines[_p["start_step"] - 1 : _p["end_step"]])
                step_df = pd.read_csv(io.StringIO(_step_text), sep="\t", decimal=",")
                step_df.columns = step_df.columns.str.strip()
                for _c in step_df.columns[1:]:
                    step_df[_c] = pd.to_numeric(step_df[_c], errors="coerce")
                _t_col    = step_df.columns[_p["col_step_time"] - 1]     if _p["col_step_time"] > 0     else step_df.columns[1]
                _zeit_col = df_raw.columns[_p["col_time"] - 1]           if _p["col_time"] > 0           else df_raw.columns[1]
                _rpm_col  = step_df.columns[_p["col_step_inactive"] - 1] if _p["col_step_inactive"] > 0  else None
                step_df["Endzeit [s]"] = step_df[_t_col].shift(-1)
                step_df.loc[step_df.index[-1], "Endzeit [s]"] = df_raw[_zeit_col].max()
                if _t_col != "Startzeit [s]":
                    step_df = step_df.rename(columns={_t_col: "Startzeit [s]"})
                step_df["inactive"] = step_df[_rpm_col] == 0 if _rpm_col else False

            load_msg = mo.callout(
                mo.md(f"**{file_upload.value[0].name}** — {len(df_raw):,} rows, {len(df_raw.columns)} columns: `{list(df_raw.columns)}`"),
                kind="success",
            )
        except Exception as _e:
            load_msg = mo.callout(mo.md(f"**Error:** {_e}"), kind="danger")
    return df_raw, load_msg, step_df


@app.cell
def _(mo):
    col_time          = mo.ui.text(label="", value="1")
    col_left          = mo.ui.text(label="", value="14")
    col_right         = mo.ui.text(label="", value="15")
    col_load          = mo.ui.text(label="", value="4")
    col_step_time     = mo.ui.text(label="", value="0")
    col_step_inactive = mo.ui.text(label="", value="0")
    return col_left, col_load, col_right, col_step_inactive, col_step_time, col_time


@app.cell
def _(cof_calc, col_left, col_load, col_right, col_time, df_raw, get_offset, mo, nlc, step_df, utility_functions):
    df_display = None
    display_msg = None
    if df_raw is not None:
        try:
            _cols = df_raw.columns
            _rename = {}
            if int(col_time.value)  > 0: _rename[_cols[int(col_time.value)  - 1]] = "Zeit"
            if int(col_left.value)  > 0: _rename[_cols[int(col_left.value)  - 1]] = "RK OFT Links"
            if int(col_right.value) > 0: _rename[_cols[int(col_right.value) - 1]] = "RK OFT Rechts"
            if int(col_load.value)  > 0: _rename[_cols[int(col_load.value)  - 1]] = "Belastung"
            df_display = df_raw.rename(columns=_rename).copy()
            _nlc = float(nlc.value) if nlc.value else None
            df_display = cof_calc.calculate(df_display, _nlc)
            if get_offset():
                df_display = utility_functions.offset(df_display, step_df)
        except Exception as _e:
            df_display = None
            display_msg = mo.callout(mo.md(f"**CoF Error:** {_e}"), kind="danger")
    return df_display, display_msg


@app.cell
def _(df_display, get_filter_params, mo, step_df, utility_functions):
    df_proc = df_display.copy() if df_display is not None else None
    _fparams = get_filter_params()
    if df_display is not None and _fparams is not None:
        try:
            _w = _fparams["filter_points"]
            if _w > 1:
                df_proc = utility_functions.filter(df_display.copy(), step_df, _w)
        except Exception as _e:
            mo.output.append(mo.callout(mo.md(f"**Filter error:** {_e}"), kind="danger"))
    return (df_proc,)


@app.cell
def _(cof_calc, df_display, df_proc, get_eval_params, mo):
    cof_eval = None
    eval_msg = None
    _params = get_eval_params()
    if df_proc is not None and df_display is not None and _params is not None:
        try:
            _minima = cof_calc.find_minima(df_proc)
            _cof_res = cof_calc.get_static_and_dynamic_cof(
                df_display, _minima,
                _params["static_range"], _params["dyn_min"], _params["dyn_max"],
            )
            cof_eval = {"minima": _minima, "cof_res": _cof_res}
        except Exception as _e:
            eval_msg = mo.callout(mo.md(f"**Evaluate error:** {_e}"), kind="danger")
    return cof_eval, eval_msg


@app.cell
def _(cof_eval, df_display, df_proc, get_filter_params, go, mo, step_df):
    import io as _io, re as _re, json as _json

    if df_display is None:
        cof_chart = mo.Html(
            '<div style="height:360px;display:flex;align-items:center;justify-content:center;'
            'background:#fafafa;border-radius:6px;color:#bbb;font-size:13px">'
            "Upload a file to see the chart</div>"
        )
    else:
        # ── A: data prep ─────────────────────────────────────────────────────
        _fparams = get_filter_params()
        _filter_active = (
            _fparams is not None
            and _fparams.get("filter_points", 1) > 1
            and df_proc is not None
        )

        # ── B: build figure ───────────────────────────────────────────────────
        _fig = go.Figure()

        # Line traces — Scattergl uses WebGL: handles large datasets efficiently in the browser
        _fig.add_trace(go.Scattergl(
            x=df_display["Zeit"], y=df_display["CoF"],
            mode="lines", name="CoF",
            line=dict(color="rgba(41,128,185,0.35)" if _filter_active else "#2980b9", width=2),
        ))
        if _filter_active:
            _fig.add_trace(go.Scattergl(
                x=df_proc["Zeit"], y=df_proc["CoF"],
                mode="lines", name="Filtered CoF",
                line=dict(color="#e67e22", width=1.5),
            ))

        # Evaluation markers — regular Scatter (few points; needs full symbol support)
        if cof_eval is not None:
            _mn = cof_eval["minima"]
            _cr = cof_eval["cof_res"]
            _fig.add_trace(go.Scatter(
                x=_mn["Min Zeit"], y=[0] * len(_mn),
                mode="markers", name="Zero crossings",
                marker=dict(symbol="line-ns", size=10, color="#888",
                            line=dict(color="#888", width=1.5)),
            ))
            _fig.add_trace(go.Scatter(
                x=_cr["staticCoFTime"], y=_cr["staticCoF"],
                mode="markers", name="Static CoF",
                marker=dict(symbol="circle", size=7, color="#e74c3c",
                            line=dict(color="#c0392b", width=1)),
            ))
            _fig.add_trace(go.Scatter(
                x=_cr["dynamicCoFTime"], y=_cr["dynamicCoF"],
                mode="markers", name="Dynamic CoF",
                marker=dict(symbol="diamond", size=7, color="#2ecc71",
                            line=dict(color="#27ae60", width=1)),
            ))
            _fig.add_trace(go.Scatter(
                x=_cr["startdynamicTime"], y=_cr["startdynamicCoF"],
                mode="markers", name="Dynamic start",
                marker=dict(symbol="triangle-right", size=8, color="#9b59b6",
                            line=dict(color="#8e44ad", width=1)),
            ))
            _fig.add_trace(go.Scatter(
                x=_cr["enddynamicTime"], y=_cr["enddynamicCoF"],
                mode="markers", name="Dynamic end",
                marker=dict(symbol="triangle-left", size=8, color="#1abc9c",
                            line=dict(color="#16a085", width=1)),
            ))

        # Step boundary vertical lines
        if step_df is not None:
            for _, _r in step_df.iterrows():
                if not _r["inactive"]:
                    for _t in [_r["Startzeit [s]"], _r["Endzeit [s]"]]:
                        _fig.add_vline(x=_t, line=dict(color="#ccc", dash="dot", width=1))

        _fig.update_layout(
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

        # ── C: iframe with x-zoom persistence ────────────────────────────────
        # CDN URL is pinned to the installed plotly version (avoids version mismatch).
        _buf = _io.StringIO()
        _fig.write_html(_buf, include_plotlyjs="cdn", full_html=False)
        _m = _re.search(r'src="(https://cdn\.plot\.ly/plotly[^"]+\.min\.js)"', _buf.getvalue())
        _cdn = _m.group(1) if _m else "https://cdn.plot.ly/plotly-latest.min.js"

        _fig_dict = _json.loads(_fig.to_json())
        _d = _json.dumps(_fig_dict["data"])
        _l = _json.dumps(_fig_dict["layout"])

        # srcdoc iframe: scripts execute, same origin as parent so window.parent is accessible.
        # __cofXR on the parent window stores the x-axis zoom range across cell re-renders.
        _iframe_html = f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<style>body{{margin:0;overflow:hidden}}</style>
<script src="{_cdn}"></script>
</head><body>
<div id="c" style="width:100vw;height:420px"></div>
<script>
var d={_d}, l={_l};
window.onload = function() {{
  var xr; try {{ xr = window.parent.__cofXR; }} catch(e) {{}}
  if (xr) {{ l.xaxis = l.xaxis || {{}}; l.xaxis.range = xr; l.xaxis.autorange = false; }}
  Plotly.react("c", d, l, {{ scrollZoom: true, displayModeBar: true, responsive: true }})
    .then(function() {{
      document.getElementById("c").on("plotly_relayout", function(e) {{
        if ("xaxis.range[0]" in e) {{
          try {{ window.parent.__cofXR = [e["xaxis.range[0]"], e["xaxis.range[1]"]]; }} catch(ex) {{}}
        }} else if (e["xaxis.autorange"]) {{
          try {{ window.parent.__cofXR = null; }} catch(ex) {{}}
        }}
      }});
    }});
}};
</script>
</body></html>"""

        _srcdoc = _iframe_html.replace("&", "&amp;").replace("<", "&lt;").replace("'", "&#39;")
        cof_chart = mo.Html(
            f"<iframe srcdoc='{_srcdoc}' style='width:100%;height:440px;border:none;display:block'></iframe>"
        )
    return (cof_chart,)


@app.cell
def _(cof_eval, df_display, df_proc, get_filter_params, mo, stat_funcs, step_df):
    import pandas as _pd
    import numpy as _np

    if df_display is None:
        results_panel = mo.Html(
            '<div style="height:60px;display:flex;align-items:center;justify-content:center;'
            'color:#bbb;font-size:13px">Click Calculate to see results</div>'
        )
    else:
        _N = len(df_display)
        _fparams = get_filter_params()
        _filter_active = (
            _fparams is not None
            and _fparams.get("filter_points", 1) > 1
            and df_proc is not None
        )

        def _p(arr):
            lst = list(arr)
            return lst + [_np.nan] * (_N - len(lst))

        # ── Always present (after Calculate) ─────────────────────────────────
        _cols = {
            "Time [s]":    list(df_display["Zeit"]),
            "CoF":         list(df_display["CoF"]),
        }

        # ── Added after Filter ────────────────────────────────────────────────
        if _filter_active:
            _cols["Filtered CoF"] = list(df_proc["CoF"])

        # ── Added after Evaluate ──────────────────────────────────────────────
        if cof_eval is not None:
            try:
                _sdf = step_df if step_df is not None else _pd.DataFrame({
                    "Startzeit [s]": [df_display["Zeit"].min()],
                    "Endzeit [s]":   [df_display["Zeit"].max()],
                    "inactive":      [False],
                })
                _stats = stat_funcs.CoF_Stat(cof_eval["cof_res"], _sdf)
                _cr = cof_eval["cof_res"]
                _mn = cof_eval["minima"]
                _cols.update({
                    "Static CoF":                  _p(_cr["staticCoF"]),
                    "Static CoF time [s]":         _p(_cr["staticCoFTime"]),
                    "Dynamic CoF":                 _p(_cr["dynamicCoF"]),
                    "Dynamic CoF time [s]":        _p(_cr["dynamicCoFTime"]),
                    "Dynamic std dev":             _p(_cr["dynamicCoFSD"]),
                    "Dynamic N":                   _p(_cr["dynamicCoFn"]),
                    "Dynamic CoF sum":             _p(_cr["dynamicCoFsigma"]),
                    "Dynamic CoF variance":        _p(_cr["dynamicCoFvariance"]),
                    "Time range [s]":              _p(_stats["Time Range"]),
                    "Static mean CoF":             _p(_stats["Static Avg"]),
                    "Static std dev":              _p(_stats["Static Std Dev"]),
                    "Static N":                    _p(_stats["Static N"]),
                    "Static CoF sum":              _p(_stats["Static Avg x N"]),
                    "Static CoF variance":         _p(_stats["Static Var"]),
                    "Dynamic mean CoF":            _p(_stats["Dynamic Avg"]),
                    "Dynamic mean std dev":        _p(_stats["Dynamic Std Dev"]),
                    "Dynamic mean N":              _p(_stats["Dynamic N"]),
                    "Dynamic CoF avg×N":           _p(_stats["Dynamic Avg x N"]),
                    "Dynamic CoF var (step)":      _p(_stats["Dynamic Var"]),
                    "-Min time [s]":               _p(_mn["-Min Zeit"]),
                    "-Min CoF":                    _p(_mn["-Min CoF"]),
                    "+Min time [s]":               _p(_mn["+Min Zeit"]),
                    "+Min CoF":                    _p(_mn["+Min CoF"]),
                    "Min time [s]":                _p(_mn["Min Zeit"]),
                    "CoF minima":                  _p(_mn["Min CoF"]),
                    "Dynamic start time [s]":      _p(_cr["startdynamicTime"]),
                    "Dynamic start CoF":           _p(_cr["startdynamicCoF"]),
                    "Dynamic end time [s]":        _p(_cr["enddynamicTime"]),
                    "Dynamic end CoF":             _p(_cr["enddynamicCoF"]),
                })
            except Exception as _e:
                _cols["Eval error"] = [str(_e)] + [_np.nan] * (_N - 1)

        try:
            results_panel = mo.vstack([
                mo.Html('<p class="panel-title">Results</p>'),
                mo.ui.table(
                    _pd.DataFrame(_cols),
                    pagination=True,
                    show_column_summaries=False,
                    show_data_types=False,
                ),
            ], gap=1)
        except Exception as _e:
            results_panel = mo.callout(mo.md(f"Results error: {_e}"), kind="warn")
    return (results_panel,)


@app.cell
def _(
    calculate_btn,
    cof_chart,
    col_left,
    col_load,
    col_right,
    col_step_inactive,
    col_step_time,
    col_time,
    df_display,
    df_proc,
    df_raw,
    display_msg,
    dyn_max,
    dyn_min,
    end_step_row,
    eval_msg,
    evaluate_btn,
    file_upload,
    filter_btn,
    filter_points,
    has_step,
    load_msg,
    mo,
    nlc,
    offset_btn,
    results_panel,
    start_main_row,
    start_step_row,
    static_range,
    stop_main_row,
):
    _navbar = mo.Html("""
    <div class="navbar">
      <div><span class="navbar-title">FRICTION EVALUATION</span><span class="navbar-version">v2.0</span></div>
      <span class="navbar-user">Marimo</span>
    </div>
    """)

    # ── Raw Data tab ──────────────────────────────────────────────────────────
    _rvm_test = (
        file_upload.value[0].name.replace(".txt", "")
        if file_upload.value else "—"
    )

    if file_upload.value:
        import pandas as _pd
        _lines = file_upload.value[0].contents.decode("latin-1").splitlines()
        _total = len(_lines)
        _rows = [line.split("\t") for line in _lines]
        _ncols = max(len(r) for r in _rows)
        _rows_padded = [r + [""] * (_ncols - len(r)) for r in _rows]
        _df_file = _pd.DataFrame(_rows_padded, columns=[str(i) for i in range(_ncols)])
        _df_file.insert(0, "#", range(1, len(_lines) + 1))
        _justify = {col: "left" for col in _df_file.columns}
        _raw_table = mo.vstack([
            mo.callout(mo.md(f"**{_total:,}** lines"), kind="info"),
            mo.ui.table(
                _df_file,
                pagination=True,
                show_column_summaries=False,
                show_data_types=False,
                text_justify_columns=_justify,
            ),
        ], gap=1)
    else:
        _raw_table = mo.Html(
            '<div style="height:200px;display:flex;align-items:center;justify-content:center;'
            'color:#bbb;font-size:13px">No data loaded</div>'
        )

    _rawdata_tab = mo.vstack([
        mo.hstack([file_upload], justify="start"),
        mo.Html('<hr class="divider">'),
        mo.Html(f'<div style="display:flex;flex-direction:column;gap:2px">'
                f'<span style="font-size:0.6rem;color:#999;font-weight:700;letter-spacing:1px">RVM TEST</span>'
                f'<span style="font-size:0.9rem;font-weight:600;color:#1f2a40">{_rvm_test}</span></div>'),
        mo.Html('<hr class="divider">'),
        mo.hstack([mo.Html('<span style="font-size:0.82rem;color:#444;min-width:160px">Normal Load Correction</span>'), nlc], align="center", justify="start", gap=2),
        mo.Html('<hr class="divider">'),
        has_step,
        mo.hstack([mo.Html('<span style="font-size:0.82rem;color:#444;min-width:160px">Start Step</span>'),      start_step_row], align="center", justify="start", gap=2),
        mo.hstack([mo.Html('<span style="font-size:0.82rem;color:#444;min-width:160px">End Step</span>'),        end_step_row],   align="center", justify="start", gap=2),
        mo.hstack([mo.Html('<span style="font-size:0.82rem;color:#444;min-width:160px">Start Main Data</span>'), start_main_row], align="center", justify="start", gap=2),
        mo.hstack([mo.Html('<span style="font-size:0.82rem;color:#444;min-width:160px">Stop Main Data</span>'),  stop_main_row],  align="center", justify="start", gap=2),
        mo.Html('<hr class="divider">'),
        mo.hstack([mo.Html('<span style="font-size:0.82rem;color:#444;min-width:160px">Time col #</span>'),          col_time],          align="center", justify="start", gap=2),
        mo.hstack([mo.Html('<span style="font-size:0.82rem;color:#444;min-width:160px">Friction Left col #</span>'), col_left],          align="center", justify="start", gap=2),
        mo.hstack([mo.Html('<span style="font-size:0.82rem;color:#444;min-width:160px">Friction Right col #</span>'),col_right],         align="center", justify="start", gap=2),
        mo.hstack([mo.Html('<span style="font-size:0.82rem;color:#444;min-width:160px">Normal Load col #</span>'),   col_load],          align="center", justify="start", gap=2),
        mo.hstack([mo.Html('<span style="font-size:0.82rem;color:#444;min-width:160px">Step Time col #</span>'),     col_step_time],     align="center", justify="start", gap=2),
        mo.hstack([mo.Html('<span style="font-size:0.82rem;color:#444;min-width:160px">Step Inactive col #</span>'), col_step_inactive], align="center", justify="start", gap=2),
        mo.Html('<hr class="divider">'),
        calculate_btn,
        mo.Html('<hr class="divider">'),
        load_msg,
        display_msg if display_msg is not None else mo.Html(''),
        _raw_table,
    ], gap=2)

    # ── CoF Analysis tab ──────────────────────────────────────────────────────
    _analysis_tab = mo.vstack([
        mo.hstack([
            mo.Html('<p class="section-label" style="margin:0;align-self:center">ACTIONS</p>'),
            offset_btn,
            filter_btn,
            evaluate_btn if df_display is not None else mo.Html(
                '<button disabled style="opacity:0.35;cursor:not-allowed;padding:4px 14px;'
                'border-radius:4px;background:#2ecc71;color:#fff;border:none;font-size:13px;'
                'font-weight:500">Evaluate</button>'
            ),
            mo.Html('<div style="width:1px;background:#eee;height:28px;margin:0 8px;align-self:center"></div>'),
            mo.Html('<p class="section-label" style="margin:0;align-self:center">PARAMETERS</p>'),
            mo.hstack([mo.Html('<span style="font-size:0.82rem;color:#444;white-space:nowrap">NLC</span>'), nlc], align="center", gap=2),
            mo.hstack([mo.Html('<span style="font-size:0.82rem;color:#444;white-space:nowrap">Filter pts</span>'), filter_points], align="center", gap=2),
            mo.hstack([mo.Html('<span style="font-size:0.82rem;color:#444;white-space:nowrap">Static %</span>'), static_range], align="center", gap=2),
            mo.hstack([mo.Html('<span style="font-size:0.82rem;color:#444;white-space:nowrap">Dyn min %</span>'), dyn_min], align="center", gap=2),
            mo.hstack([mo.Html('<span style="font-size:0.82rem;color:#444;white-space:nowrap">Dyn max %</span>'), dyn_max], align="center", gap=2),
        ], gap=3, align="end"),
        mo.Html('<hr class="divider">'),
        mo.vstack([
            mo.Html('<p class="panel-title">Analysis Visualization</p>'),
            display_msg if display_msg is not None else mo.Html(''),
            eval_msg if eval_msg is not None else mo.Html(''),
            cof_chart,
            mo.Html('<hr class="divider">'),
            results_panel,
        ], gap=1),
    ], gap=2)

    mo.vstack([
        _navbar,
        mo.ui.tabs({
            "📋  Raw Data":      _rawdata_tab,
            "📊  CoF Analysis":  _analysis_tab,
        }),
    ], gap=0)
    return


if __name__ == "__main__":
    app.run()
