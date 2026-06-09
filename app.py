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
        background: #1f2a40;
        padding: 0 24px;
        height: 50px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-bottom: 1px solid #2d3748;
        border-radius: 8px 8px 0 0;
      }
      .navbar-title { color: #4cceac; font-weight: 700; font-size: 1rem; letter-spacing: 0.5px; }
      .navbar-version { color: #fff; font-size: 0.75rem; margin-left: 10px; }
      .navbar-user { color: #aaa; font-size: 0.8rem; }
      .panel {
        background: #fff;
        border-radius: 8px;
        padding: 16px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.08);
      }
      .panel-title { font-weight: 700; color: #1f2a40; font-size: 0.85rem; margin: 0 0 12px 0; }
      .section-label { font-weight: 700; color: #999; font-size: 0.6rem; letter-spacing: 1px; margin: 0 0 6px 0; }
      .divider { border: none; border-top: 1px solid #eee; margin: 10px 0; }
      .upload-wrapper { display: flex; flex-direction: column; align-items: center; padding: 48px 20px; gap: 16px; }
      .upload-title { color: #1f2a40; font-size: 1.05rem; font-weight: 600; margin: 0; }
      .analysis-layout { display: flex; gap: 16px; align-items: flex-start; padding: 8px; }
      .controls-panel { width: 195px; min-width: 195px; flex-shrink: 0; }
      .main-panel { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 12px; }
    </style>
    """)
    return


@app.cell
def _(mo):
    file_upload = mo.ui.file(label="Upload test file (.txt)", filetypes=[".txt"])
    data_origin = mo.ui.dropdown(
        ["OFT", "SRV", "SRV_FSA"], value="OFT", label="Data origin"
    )
    return data_origin, file_upload


@app.cell
def _(mo):
    apply_offset  = mo.ui.switch(label="Apply Offset", value=True)
    filter_points = mo.ui.number(label="Filter Points", value=25, step=1)
    nlc           = mo.ui.number(label="Normal Load Correction", value=0.0, step=0.1)
    static_range  = mo.ui.number(label="Static CoF Range (%)", value=10.0, step=1.0)
    dyn_min       = mo.ui.number(label="Dyn CoF Min (%)", value=20.0, step=1.0)
    dyn_max       = mo.ui.number(label="Dyn CoF Max (%)", value=80.0, step=1.0)
    return apply_offset, dyn_max, dyn_min, filter_points, nlc, static_range


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
def _(
    apply_offset,
    cof_calc,
    df_raw,
    filter_points,
    nlc,
    step_df,
    utility_functions,
):
    df_proc = None
    if df_raw is not None:
        df_proc = df_raw.copy()
        _nlc = nlc.value if nlc.value != 0 else None
        df_proc = cof_calc.calculate(df_proc, _nlc)
        if apply_offset.value:
            df_proc = utility_functions.offset(df_proc, step_df)
        _w = int(filter_points.value)
        if _w > 1:
            df_proc = utility_functions.filter(df_proc, step_df, _w)
    return (df_proc,)


@app.cell
def _(df_proc, go, mo, step_df):
    if df_proc is None:
        cof_chart = mo.Html(
            '<div style="height:360px;display:flex;align-items:center;justify-content:center;'
            'background:#fafafa;border-radius:6px;color:#bbb;font-size:13px">'
            "Upload a file to see the chart</div>"
        )
    else:
        _y_min = float(df_proc["CoF"].min())
        _y_max = float(df_proc["CoF"].max())
        _y_pad = max(abs(_y_max - _y_min) * 0.05, 0.001)

        _fig = go.Figure()
        _fig.add_trace(go.Scatter(
            x=df_proc["Zeit [s]"], y=df_proc["CoF"],
            mode="lines", name="CoF", line=dict(color="#4A90D9", width=1),
        ))
        if step_df is not None:
            for _, _r in step_df.iterrows():
                if not _r["inactive"]:
                    for _t in [_r["Startzeit [s]"], _r["Endzeit [s]"]]:
                        _fig.add_vline(x=_t, line=dict(color="#ccc", dash="dot", width=1))
        _fig.update_layout(
            height=360,
            xaxis_title="Time [s]", yaxis_title="CoF [-]",
            margin=dict(l=60, r=20, t=20, b=50),
            plot_bgcolor="#fff", paper_bgcolor="#fff",
            font=dict(color="#1f2a40", size=12),
            dragmode="pan",
            xaxis=dict(gridcolor="#efefef", linecolor="#ddd"),
            yaxis=dict(
                range=[_y_min - _y_pad, _y_max + _y_pad],
                fixedrange=True,
                gridcolor="#efefef", linecolor="#ddd",
            ),
        )
        cof_chart = mo.ui.plotly(_fig, config={"scrollZoom": True, "displayModeBar": True})
    return (cof_chart,)


@app.cell
def _(df_proc, go, mo):
    if df_proc is None or "stroke" not in df_proc.columns:
        stroke_chart = mo.Html("")
    else:
        _sy_min = float(df_proc["stroke"].min())
        _sy_max = float(df_proc["stroke"].max())
        _sy_pad = max(abs(_sy_max - _sy_min) * 0.05, 0.001)

        _fig2 = go.Figure()
        _fig2.add_trace(go.Scatter(
            x=df_proc["Zeit [s]"], y=df_proc["stroke"],
            mode="lines", name="Stroke", line=dict(color="#e67e22", width=1),
        ))
        _fig2.update_layout(
            height=200,
            xaxis_title="Time [s]", yaxis_title="Stroke [mm]",
            margin=dict(l=60, r=20, t=20, b=50),
            plot_bgcolor="#fff", paper_bgcolor="#fff",
            font=dict(color="#1f2a40", size=12),
            dragmode="pan",
            xaxis=dict(gridcolor="#efefef", linecolor="#ddd"),
            yaxis=dict(
                range=[_sy_min - _sy_pad, _sy_max + _sy_pad],
                fixedrange=True,
                gridcolor="#efefef", linecolor="#ddd",
            ),
        )
        stroke_chart = mo.ui.plotly(_fig2, config={"scrollZoom": True, "displayModeBar": True})
    return (stroke_chart,)


@app.cell
def _(
    cof_calc,
    df_proc,
    dyn_max,
    dyn_min,
    mo,
    stat_funcs,
    static_range,
    step_df,
):
    if df_proc is None:
        results_panel = mo.Html(
            '<div style="height:80px;display:flex;align-items:center;justify-content:center;'
            'color:#bbb;font-size:13px">Results will appear after file is loaded</div>'
        )
    else:
        try:
            _minima  = cof_calc.find_minima(df_proc)
            _cof_res = cof_calc.get_static_and_dynamic_cof(
                df_proc, _minima, static_range.value, dyn_min.value, dyn_max.value
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
    apply_offset,
    cof_chart,
    data_origin,
    dyn_max,
    dyn_min,
    file_upload,
    filter_points,
    load_msg,
    mo,
    nlc,
    results_panel,
    static_range,
    stroke_chart,
):
    _navbar = mo.Html("""
    <div class="navbar">
      <div>
        <span class="navbar-title">FRICTION EVALUATION</span>
        <span class="navbar-version">v2.0</span>
      </div>
      <span class="navbar-user">Marimo</span>
    </div>
    """)

    # Upload tab
    _upload_tab = mo.vstack([
        mo.Html('<p class="upload-title">Upload your file to continue</p>'),
        file_upload,
        data_origin,
        load_msg,
    ], align="center", gap=2)

    # Controls panel
    _controls = mo.vstack([
        mo.Html('<p class="section-label">ACTIONS</p>'),
        apply_offset,
        mo.Html('<hr class="divider">'),
        mo.Html('<p class="section-label">PARAMETERS</p>'),
        nlc,
        filter_points,
        mo.Html('<hr class="divider">'),
        static_range,
        dyn_min,
        dyn_max,
    ], gap=1)

    # Analysis tab
    _analysis_tab = mo.hstack([
        mo.vstack([
            mo.Html('<p class="panel-title">Controls</p>'),
            _controls,
        ], gap=0),
        mo.vstack([
            mo.Html('<p class="panel-title">Analysis Visualization</p>'),
            cof_chart,
            stroke_chart,
            mo.Html('<hr class="divider">'),
            results_panel,
        ], gap=1),
    ], gap=2, align="start")

    mo.vstack([
        _navbar,
        mo.tabs({
            "📂  Upload Data": _upload_tab,
            "📊  CoF Analysis": _analysis_tab,
        }),
    ], gap=0)
    return


if __name__ == "__main__":
    app.run()
