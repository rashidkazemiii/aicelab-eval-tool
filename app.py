import marimo

__generated_with = "0.13.0"
app = marimo.App(width="full", title="CoF Evaluation Tool")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import numpy as np
    import plotly.graph_objects as go
    import sys
    import os
    import tempfile

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
    return go, mo, np, os, pd, sys, tempfile


@app.cell
def _():
    from read_files.load import load_data
    from physics import CoF as cof_calc
    from physics import utility_functions
    from physics import statistics as stat_funcs
    return cof_calc, load_data, stat_funcs, utility_functions


@app.cell
def _(mo):
    mo.md("# CoF Evaluation Tool")
    return


@app.cell
def _(mo):
    file_upload = mo.ui.file(label="Upload test file", filetypes=[".txt"])
    data_origin = mo.ui.dropdown(
        ["OFT", "SRV", "SRV_FSA"], value="OFT", label="Data origin"
    )
    mo.hstack([file_upload, data_origin], gap=2)
    return data_origin, file_upload


@app.cell
def _(mo):
    normal_load_correction = mo.ui.number(
        label="Normal Load Correction (0 = none)", value=0.0, step=0.1
    )
    filter_window = mo.ui.slider(
        1, 201, step=2, value=15, label="Filter Window", show_value=True
    )
    apply_offset = mo.ui.switch(label="Apply Offset", value=True)
    static_range = mo.ui.slider(
        1, 50, value=20, label="Static CoF Range %", show_value=True
    )
    dyn_min = mo.ui.slider(
        1, 99, value=20, label="Dynamic Start %", show_value=True
    )
    dyn_max = mo.ui.slider(
        1, 99, value=80, label="Dynamic End %", show_value=True
    )
    mo.vstack(
        [
            mo.hstack([normal_load_correction, filter_window, apply_offset], gap=4),
            mo.hstack([static_range, dyn_min, dyn_max], gap=4),
        ],
        gap=2,
    )
    return apply_offset, dyn_max, dyn_min, filter_window, normal_load_correction, static_range


@app.cell
def _(data_origin, file_upload, load_data, mo, os, tempfile):
    df_raw = None
    step_df = None
    header = None
    _status = None

    if file_upload.value:
        f = file_upload.value[0]
        suffix = os.path.splitext(f.name)[-1] or ".txt"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(f.contents)
            _tmppath = tmp.name
        try:
            df_raw, step_df, header = load_data(_tmppath, data_origin.value)
            _status = mo.callout(
                mo.md(f"Loaded **{f.name}** — {len(df_raw):,} rows"), kind="success"
            )
        except Exception as e:
            _status = mo.callout(mo.md(f"Error loading file: {e}"), kind="danger")

    _status
    return df_raw, header, step_df


@app.cell
def _(
    apply_offset,
    cof_calc,
    df_raw,
    filter_window,
    normal_load_correction,
    step_df,
    utility_functions,
):
    df_proc = None
    if df_raw is not None:
        df_proc = df_raw.copy()
        nlc = normal_load_correction.value if normal_load_correction.value != 0 else None
        df_proc = cof_calc.calculate(df_proc, nlc)
        if apply_offset.value:
            df_proc = utility_functions.offset(df_proc, step_df)
        if filter_window.value > 1:
            df_proc = utility_functions.filter(df_proc, step_df, filter_window.value)
    return (df_proc,)


@app.cell
def _(df_proc, go, mo, step_df):
    if df_proc is None:
        mo.md("*Upload a file to see the charts.*")
    else:
        _fig = go.Figure()
        _fig.add_trace(
            go.Scatter(
                x=df_proc["Zeit [s]"],
                y=df_proc["CoF"],
                mode="lines",
                name="CoF",
                line=dict(color="steelblue", width=1),
            )
        )
        if step_df is not None:
            for _, _row in step_df.iterrows():
                if not _row["inactive"]:
                    for _t in [_row["Startzeit [s]"], _row["Endzeit [s]"]]:
                        _fig.add_vline(
                            x=_t,
                            line=dict(color="gray", dash="dot", width=1),
                        )
        _fig.update_layout(
            title="CoF vs Time",
            xaxis_title="Time [s]",
            yaxis_title="CoF",
            height=400,
            margin=dict(l=60, r=20, t=50, b=50),
        )
        mo.ui.plotly(_fig)
    return


@app.cell
def _(df_proc, go, mo):
    if df_proc is not None and "stroke" in df_proc.columns:
        _fig2 = go.Figure()
        _fig2.add_trace(
            go.Scatter(
                x=df_proc["Zeit [s]"],
                y=df_proc["stroke"],
                mode="lines",
                name="Stroke",
                line=dict(color="coral", width=1),
            )
        )
        _fig2.update_layout(
            title="Stroke vs Time",
            xaxis_title="Time [s]",
            yaxis_title="Stroke [mm]",
            height=300,
            margin=dict(l=60, r=20, t=50, b=50),
        )
        mo.ui.plotly(_fig2)
    return


@app.cell
def _(cof_calc, df_proc, dyn_max, dyn_min, mo, stat_funcs, static_range, step_df):
    if df_proc is not None:
        try:
            _minima = cof_calc.find_minima(df_proc)
            _cof_result = cof_calc.get_static_and_dynamic_cof(
                df_proc,
                _minima,
                static_range.value,
                dyn_min.value,
                dyn_max.value,
            )
            _stats = stat_funcs.CoF_Stat(_cof_result, step_df)
            mo.vstack(
                [
                    mo.md("## Results"),
                    mo.ui.table(_stats),
                ]
            )
        except Exception as e:
            mo.callout(mo.md(f"Evaluation error: {e}"), kind="warn")
    return


if __name__ == "__main__":
    app.run()
