import marimo

__generated_with = "0.23.9"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import plotly.graph_objects as go
    import sys, os, tempfile

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

    from read_files.load import load_data
    from physics import CoF as cof_calc
    from physics import utility_functions
    from physics import statistics as stat_funcs

    return (
        cof_calc,
        go,
        load_data,
        mo,
        os,
        stat_funcs,
        tempfile,
        utility_functions,
    )


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
    </style>
    """)
    return


@app.cell
def _(mo):
    get_eval_params, set_eval_params = mo.state(None)
    return get_eval_params, set_eval_params


@app.cell
def _(mo):
    file_upload = mo.ui.file(label="Upload test file (.txt)", filetypes=[".txt"])
    data_origin = mo.ui.dropdown(["OFT", "SRV", "SRV_FSA"], value="OFT", label="Data origin")
    return data_origin, file_upload


@app.cell
def _(mo):
    stepwise_check = mo.ui.number(label="Stepwise Check", value=1, step=1)
    nlc            = mo.ui.number(label="Normal Load Correction", value=0.0,  step=0.1)
    offset_btn     = mo.ui.button(label="Offset",   kind="neutral", value=0)
    filter_points  = mo.ui.number(label="Filter Points",          value=25,   step=1)
    static_range   = mo.ui.number(label="Static CoF Range (%)",   value=10.0, step=1.0)
    dyn_min        = mo.ui.number(label="Dyn CoF Min (%)",        value=20.0, step=1.0)
    dyn_max        = mo.ui.number(label="Dyn CoF Max (%)",        value=80.0, step=1.0)
    return dyn_max, dyn_min, filter_points, nlc, offset_btn, static_range, stepwise_check


@app.cell
def _(dyn_max, dyn_min, filter_points, mo, nlc, set_eval_params, static_range):
    evaluate_btn = mo.ui.button(
        label="Evaluate",
        kind="success",
        on_click=lambda _: set_eval_params({
            "filter_points": int(filter_points.value),
            "nlc":           float(nlc.value),
            "static_range":  float(static_range.value),
            "dyn_min":       float(dyn_min.value),
            "dyn_max":       float(dyn_max.value),
        }),
    )
    return (evaluate_btn,)


@app.cell
def _(data_origin, file_upload, load_data, mo, os, tempfile):
    df_raw  = None
    step_df = None
    load_msg = mo.callout(mo.md("Upload a `.txt` file to begin."), kind="info")

    if file_upload.value:
        _f = file_upload.value[0]
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=os.path.splitext(_f.name)[-1] or ".txt"
        ) as _t:
            _t.write(_f.contents)
            _path = _t.name
        try:
            df_raw, step_df, _ = load_data(_path, data_origin.value)
            load_msg = mo.callout(
                mo.md(f"**{_f.name}** — {len(df_raw):,} rows loaded"), kind="success"
            )
        except Exception as _e:
            load_msg = mo.callout(mo.md(f"**Error:** {_e}"), kind="danger")
    return df_raw, load_msg, step_df


@app.cell
def _(cof_calc, df_raw, mo, nlc, offset_btn, step_df, utility_functions):
    df_display = None
    if df_raw is not None:
        try:
            df_display = df_raw.copy()
            _nlc = float(nlc.value) if nlc.value else None
            df_display = cof_calc.calculate(df_display, _nlc)
            if offset_btn.value > 0:
                df_display = utility_functions.offset(df_display, step_df)
        except Exception as _e:
            df_display = None
            mo.output.append(mo.callout(mo.md(f"**Error:** {_e}"), kind="danger"))
    return (df_display,)


@app.cell
def _(df_display, get_eval_params, mo, step_df, utility_functions):
    df_proc = None
    _params = get_eval_params()
    if df_display is not None and _params is not None:
        try:
            df_proc = df_display.copy()
            _w = _params["filter_points"]
            if _w > 1:
                df_proc = utility_functions.filter(df_proc, step_df, _w)
        except Exception as _e:
            df_proc = None
            mo.output.append(mo.callout(mo.md(f"**Processing error:** {_e}"), kind="danger"))
    return (df_proc,)


@app.cell
def _(df_display, go, mo, step_df):
    if df_display is None:
        cof_chart = mo.Html(
            '<div style="height:360px;display:flex;align-items:center;justify-content:center;'
            'background:#fafafa;border-radius:6px;color:#bbb;font-size:13px">'
            "Upload a file to see the chart</div>"
        )
    else:
        _y_min = float(df_display["CoF"].min())
        _y_max = float(df_display["CoF"].max())
        _y_pad = max(abs(_y_max - _y_min) * 0.05, 0.001)
        _fig = go.Figure()
        _fig.add_trace(go.Scatter(
            x=df_display["Zeit [s]"], y=df_display["CoF"],
            mode="lines", name="CoF", line=dict(color="#4A90D9", width=1),
        ))
        if step_df is not None:
            for _, _r in step_df.iterrows():
                if not _r["inactive"]:
                    for _t in [_r["Startzeit [s]"], _r["Endzeit [s]"]]:
                        _fig.add_vline(x=_t, line=dict(color="#ccc", dash="dot", width=1))
        _fig.update_layout(
            height=380,
            xaxis_title="Time [s]", yaxis_title="CoF [-]",
            margin=dict(l=60, r=20, t=20, b=50),
            plot_bgcolor="#fff", paper_bgcolor="#fff",
            font=dict(color="#1f2a40", size=12),
            dragmode="pan",
            xaxis=dict(gridcolor="#efefef", linecolor="#ddd"),
            yaxis=dict(
                range=[_y_min - _y_pad, _y_max + _y_pad],
                fixedrange=True, gridcolor="#efefef", linecolor="#ddd",
            ),
        )
        cof_chart = mo.ui.plotly(_fig, config={"scrollZoom": True, "displayModeBar": True})
    return (cof_chart,)


@app.cell
def _(cof_calc, df_proc, get_eval_params, mo, stat_funcs, step_df):
    _params = get_eval_params()
    if df_proc is None or _params is None:
        results_panel = mo.Html(
            '<div style="height:60px;display:flex;align-items:center;justify-content:center;'
            'color:#bbb;font-size:13px">Click Evaluate to see results</div>'
        )
    else:
        try:
            _minima  = cof_calc.find_minima(df_proc)
            _cof_res = cof_calc.get_static_and_dynamic_cof(
                df_proc, _minima,
                _params["static_range"], _params["dyn_min"], _params["dyn_max"]
            )
            _stats   = stat_funcs.CoF_Stat(_cof_res, step_df)
            results_panel = mo.vstack([
                mo.Html('<p class="panel-title">Results Summary</p>'),
                mo.ui.table(_stats),
            ], gap=1)
        except Exception as _e:
            results_panel = mo.callout(mo.md(f"Evaluation error: {_e}"), kind="warn")
    return (results_panel,)


@app.cell
def _(
    cof_chart,
    data_origin,
    df_raw,
    dyn_max,
    dyn_min,
    evaluate_btn,
    file_upload,
    filter_points,
    mo,
    nlc,
    offset_btn,
    results_panel,
    static_range,
    stepwise_check,
):
    _navbar = mo.Html("""
    <div class="navbar">
      <div><span class="navbar-title">FRICTION EVALUATION</span><span class="navbar-version">v2.0</span></div>
      <span class="navbar-user">Marimo</span>
    </div>
    """)

    # ── Raw Data tab ──────────────────────────────────────────────────────────
    _col_order = [
        "Zeit [s]",
        "rotation speed",
        "normal load",
        "stroke",
        "friction force left",
        "friction force right",
        "friction force",
        "Wear",
        "CoF",
        "Temperature",
        "external temperature",
        "external displacement",
        "external pressure",
    ]
    _col_names = {
        "Zeit [s]":              "Time (s)",
        "rotation speed":        "Rotation speed (min⁻¹)",
        "normal load":           "Normal load (N)",
        "stroke":                "Stroke (mm)",
        "friction force left":   "Friction force L (N)",
        "friction force right":  "Friction force R (N)",
        "friction force":        "Friction force (N)",
        "Wear":                  "Wear (mm)",
        "CoF":                   "CoF",
        "Temperature":           "Temperature (°C)",
        "external temperature":  "External temperature (°C)",
        "external displacement": "External displacement (mm)",
        "external pressure":     "External pressure (bar)",
    }

    _rvm_test = (
        file_upload.value[0].name.replace(".txt", "")
        if file_upload.value else "—"
    )

    if df_raw is not None:
        _cols = [c for c in _col_order if c in df_raw.columns]
        _df_table = df_raw[_cols].rename(columns=_col_names)
        _raw_table = mo.ui.table(_df_table, pagination=True)
    else:
        _raw_table = mo.Html(
            '<div style="height:200px;display:flex;align-items:center;justify-content:center;'
            'color:#bbb;font-size:13px">No data loaded</div>'
        )

    _rawdata_tab = mo.vstack([
        mo.hstack([file_upload, data_origin], gap=3, align="end"),
        mo.Html('<hr class="divider">'),
        mo.hstack([
            mo.Html(f'<div style="display:flex;flex-direction:column;gap:2px">'
                    f'<span style="font-size:0.6rem;color:#999;font-weight:700;letter-spacing:1px">RVM TEST</span>'
                    f'<span style="font-size:0.9rem;font-weight:600;color:#1f2a40">{_rvm_test}</span></div>'),
            stepwise_check,
            nlc,
        ], gap=4, align="center"),
        mo.Html('<hr class="divider">'),
        _raw_table,
    ], gap=2)

    # ── CoF Analysis tab ──────────────────────────────────────────────────────
    _controls = mo.vstack([
        mo.Html('<p class="section-label">ACTIONS</p>'),
        offset_btn,
        evaluate_btn,
        mo.Html('<hr class="divider">'),
        mo.Html('<p class="section-label">PARAMETERS</p>'),
        nlc,
        filter_points,
        mo.Html('<hr class="divider">'),
        static_range,
        dyn_min,
        dyn_max,
    ], gap=1)

    _analysis_tab = mo.hstack([
        mo.vstack([
            mo.Html('<p class="panel-title">Controls</p>'),
            _controls,
        ], gap=0),
        mo.vstack([
            mo.Html('<p class="panel-title">Analysis Visualization</p>'),
            cof_chart,
            mo.Html('<hr class="divider">'),
            results_panel,
        ], gap=1),
    ], gap=2, align="start")

    mo.vstack([
        _navbar,
        mo.tabs({
            "📋  Raw Data":      _rawdata_tab,
            "📊  CoF Analysis":  _analysis_tab,
        }),
    ], gap=0)
    return


if __name__ == "__main__":
    app.run()
