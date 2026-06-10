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
      input[type="number"] { width: 72px !important; -moz-appearance: textfield; }
      input[type="number"]::-webkit-outer-spin-button,
      input[type="number"]::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
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
    return (file_upload,)


@app.cell
def _(mo):
    get_parse_params, set_parse_params = mo.state(None)
    return get_parse_params, set_parse_params


@app.cell
def _(mo):
    stepwise_check = mo.ui.number(label="Stepwise Check",         value=1,    step=1)
    nlc            = mo.ui.number(label="Normal Load Correction", value=0.0,  step=0.1)
    offset_btn     = mo.ui.button(label="Offset",   kind="neutral", value=0)
    filter_points  = mo.ui.number(label="Filter Points",          value=25,   step=1)
    static_range   = mo.ui.number(label="Static CoF Range (%)",   value=10.0, step=1.0)
    dyn_min        = mo.ui.number(label="Dyn CoF Min (%)",        value=20.0, step=1.0)
    dyn_max        = mo.ui.number(label="Dyn CoF Max (%)",        value=80.0, step=1.0)
    return dyn_max, dyn_min, filter_points, nlc, offset_btn, static_range, stepwise_check


@app.cell
def _(file_upload, mo):
    _total = (
        len(file_upload.value[0].contents.decode("latin-1").splitlines())
        if file_upload.value else 0
    )
    start_step_row = mo.ui.number(label="Start Step",      value=0,      step=1)
    end_step_row   = mo.ui.number(label="End Step",         value=0,      step=1)
    start_main_row = mo.ui.number(label="Start Main Data", value=41,     step=1)
    stop_main_row  = mo.ui.number(label="Stop Main Data",  value=_total, step=1)
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
    col_time          = mo.ui.number(label="Time col #",          value=1,  step=1)
    col_left          = mo.ui.number(label="Friction Left col #", value=14, step=1)
    col_right         = mo.ui.number(label="Friction Right col #",value=15, step=1)
    col_load          = mo.ui.number(label="Normal Load col #",   value=4,  step=1)
    col_step_time     = mo.ui.number(label="Step Time col #",     value=0, step=1)
    col_step_inactive = mo.ui.number(label="Step Inactive col #", value=0, step=1)
    return col_left, col_load, col_right, col_step_inactive, col_step_time, col_time


@app.cell
def _(cof_calc, col_left, col_load, col_right, col_time, df_raw, mo, nlc, offset_btn, step_df, utility_functions):
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
            if offset_btn.value > 0:
                df_display = utility_functions.offset(df_display, step_df)
        except Exception as _e:
            df_display = None
            display_msg = mo.callout(mo.md(f"**CoF Error:** {_e}"), kind="danger")
    return df_display, display_msg


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
        _step = max(1, len(df_display) // 5000)
        _df_chart = df_display.iloc[::_step]
        _fig = go.Figure()
        _fig.add_trace(go.Scatter(
            x=_df_chart["Zeit"], y=_df_chart["CoF"],
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
                mo.ui.table(_stats, show_column_summaries=False, show_data_types=False),
            ], gap=1)
        except Exception as _e:
            results_panel = mo.callout(mo.md(f"Evaluation error: {_e}"), kind="warn")
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
    df_raw,
    display_msg,
    dyn_max,
    dyn_min,
    end_step_row,
    evaluate_btn,
    file_upload,
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
    stepwise_check,
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
        _preview = _lines[:500]
        _rows = [line.split("\t") for line in _preview]
        _ncols = max(len(r) for r in _rows)
        _rows_padded = [r + [""] * (_ncols - len(r)) for r in _rows]
        _df_file = _pd.DataFrame(_rows_padded, columns=[str(i) for i in range(_ncols)])
        _df_file.insert(0, "#", range(1, len(_preview) + 1))
        _justify = {col: "left" for col in _df_file.columns}
        _raw_table = mo.vstack([
            mo.callout(mo.md(f"Showing first 500 of **{_total:,}** lines"), kind="info"),
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
        mo.hstack([file_upload], gap=3, align="end"),
        mo.Html('<hr class="divider">'),
        mo.hstack([
            mo.Html(f'<div style="display:flex;flex-direction:column;gap:2px">'
                    f'<span style="font-size:0.6rem;color:#999;font-weight:700;letter-spacing:1px">RVM TEST</span>'
                    f'<span style="font-size:0.9rem;font-weight:600;color:#1f2a40">{_rvm_test}</span></div>'),
            mo.Html('<div style="flex:1"></div>'),
            mo.hstack([stepwise_check, nlc], gap=2, align="end"),
        ], gap=0, align="center"),
        mo.Html('<hr class="divider">'),
        mo.Html('<p class="section-label">CONFIGURE</p>'),
        mo.hstack([
            has_step,
            start_step_row,
            end_step_row,
            start_main_row,
            stop_main_row,
            calculate_btn,
        ], gap=3, align="end"),
        mo.hstack([
            mo.Html('<p class="section-label" style="margin:0;align-self:center">COLUMNS</p>'),
            col_time,
            col_left,
            col_right,
            col_load,
            col_step_time,
            col_step_inactive,
        ], gap=3, align="end"),
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
            evaluate_btn,
            mo.Html('<div style="width:1px;background:#eee;height:28px;margin:0 8px;align-self:center"></div>'),
            mo.Html('<p class="section-label" style="margin:0;align-self:center">PARAMETERS</p>'),
            nlc,
            filter_points,
            static_range,
            dyn_min,
            dyn_max,
        ], gap=3, align="end"),
        mo.Html('<hr class="divider">'),
        mo.vstack([
            mo.Html('<p class="panel-title">Analysis Visualization</p>'),
            display_msg if display_msg is not None else mo.Html(''),
            cof_chart,
            mo.Html('<hr class="divider">'),
            results_panel,
            mo.Html('<hr class="divider">'),
            mo.Html('<p class="panel-title">CoF Data</p>'),
            mo.vstack([
                mo.callout(mo.md(f"Showing first 500 of **{len(df_display):,}** rows"), kind="info"),
                mo.ui.table(
                    df_display[["Zeit", "CoF"]].head(500).reset_index(drop=True),
                    pagination=False,
                    show_column_summaries=False,
                    show_data_types=False,
                ),
            ]) if df_display is not None and "Zeit" in df_display.columns and "CoF" in df_display.columns
            else mo.Html('<div style="color:#bbb;font-size:13px;padding:8px">No data</div>'),
        ], gap=1),
    ], gap=2)

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
