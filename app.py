import marimo

__generated_with = "0.23.9"
app = marimo.App(width="full")


# ── Imports ──────────────────────────────────────────────────────────────────
@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import plotly.graph_objects as go
    import sys, os

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

    from physics import CoF as cof_calc
    from physics import utility_functions
    from physics import statistics as stat_funcs
    import data_loader
    import table_helpers

    return cof_calc, data_loader, go, mo, pd, stat_funcs, table_helpers, utility_functions


# ── App init (database) ───────────────────────────────────────────────────────
@app.cell
def _(mo):
    import database as db_mod
    db_mod.create_tables()
    return (db_mod,)


# ── Styling ────────────────────────────────────────────────────────────────
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
        width: 80px !important;
        max-width: 80px !important;
        min-width: 0 !important;
        box-sizing: border-box !important;
      }
      label:has(input[type="text"]) {
        width: 80px !important;
        max-width: 80px !important;
        min-width: 0 !important;
        overflow: hidden !important;
      }
    </style>
    """)
    return


# ── App state ──────────────────────────────────────────────────────────────
@app.cell
def _(mo):
    get_offset, set_offset = mo.state(False)
    return get_offset, set_offset


# ── Widgets / forms ────────────────────────────────────────────────────────
@app.cell
def _(mo):
    file_upload = mo.ui.file(label="Upload test file (.txt)", filetypes=[".txt"])
    return (file_upload,)


@app.cell
def _(mo):
    def make_submit_only_form(submit_button_label, **form_kwargs):
        # Hidden field so the form has something to batch; the form's own
        # submit button is the only thing rendered, matching Filter/Evaluate's
        # chrome.
        _hidden = mo.Html(
            '<div style="visibility:hidden;height:26px">{v}</div>'
        ).batch(v=mo.ui.text(value=""))
        return _hidden.form(submit_button_label=submit_button_label, **form_kwargs)
    return (make_submit_only_form,)


@app.cell
def _(get_offset, make_submit_only_form, set_offset):
    def flip_offset(_ignored_new_value):
        set_offset(not get_offset())

    if get_offset():
        _offset_button_label = "Offset (ON)"
    else:
        _offset_button_label = "Offset"

    offset_form = make_submit_only_form(
        _offset_button_label,
        bordered=False,
        on_change=flip_offset,
    )
    return (offset_form,)


@app.cell
def _(make_submit_only_form):
    save_form = make_submit_only_form("💾 Save", bordered=False)
    return (save_form,)


@app.cell
def _(mo):
    overwrite_btn = mo.ui.run_button(label="Overwrite & Save")
    return (overwrite_btn,)


@app.cell
def _(file_upload, mo):
    # All raw-data parsing settings live in one form: nothing here takes effect
    # until "Calculate" is pressed, no matter which field was edited or how
    # (typing, tabbing away, clicking elsewhere) — mo.ui.form only publishes
    # .value on explicit submit, unlike bare mo.ui widgets which are live.
    if file_upload.value:
        _total = len(file_upload.value[0].contents.decode("latin-1").splitlines())
    else:
        _total = 0
    _raw_data_tpl = mo.Html(
        '<div style="display:flex;flex-direction:column;gap:10px">'
        '<div style="display:flex;align-items:center;gap:8px">'
        '<span style="font-size:0.82rem;color:#444;min-width:160px">Normal Load Correction</span>{nlc}</div>'
        '<hr class="divider">'
        '{has_step}'
        '<div style="display:flex;align-items:center;gap:8px">'
        '<span style="font-size:0.82rem;color:#444;min-width:160px">Start Step</span>{start_step_row}</div>'
        '<div style="display:flex;align-items:center;gap:8px">'
        '<span style="font-size:0.82rem;color:#444;min-width:160px">End Step</span>{end_step_row}</div>'
        '<div style="display:flex;align-items:center;gap:8px">'
        '<span style="font-size:0.82rem;color:#444;min-width:160px">Start Main Data</span>{start_main_row}</div>'
        '<div style="display:flex;align-items:center;gap:8px">'
        '<span style="font-size:0.82rem;color:#444;min-width:160px">Stop Main Data</span>{stop_main_row}</div>'
        '<hr class="divider">'
        '<div style="display:flex;align-items:center;gap:8px">'
        '<span style="font-size:0.82rem;color:#444;min-width:160px">Time col #</span>{col_time}</div>'
        '<div style="display:flex;align-items:center;gap:8px">'
        '<span style="font-size:0.82rem;color:#444;min-width:160px">Friction Left col #</span>{col_left}</div>'
        '<div style="display:flex;align-items:center;gap:8px">'
        '<span style="font-size:0.82rem;color:#444;min-width:160px">Friction Right col #</span>{col_right}</div>'
        '<div style="display:flex;align-items:center;gap:8px">'
        '<span style="font-size:0.82rem;color:#444;min-width:160px">Normal Load col #</span>{col_load}</div>'
        '</div>'
    )
    raw_data_form = _raw_data_tpl.batch(
        nlc=mo.ui.text(value=""),
        has_step=mo.ui.checkbox(label="Has step data", value=True),
        start_step_row=mo.ui.text(value="0"),
        end_step_row=mo.ui.text(value="0"),
        start_main_row=mo.ui.text(value="41"),
        stop_main_row=mo.ui.text(value=str(_total)),
        col_time=mo.ui.text(value="1"),
        col_left=mo.ui.text(value="14"),
        col_right=mo.ui.text(value="15"),
        col_load=mo.ui.text(value="4"),
    ).form(submit_button_label="Calculate", bordered=False)
    return (raw_data_form,)


@app.cell
def _(mo):
    # Fixed-width wrapper around each placeholder: marimo's text input is a
    # shadow-DOM web component sized at 100% of its host element, so a
    # page-level <style> width rule can never reach it — this is the only
    # way to control its rendered width.
    _filter_tpl = mo.Html(
        '<div style="display:flex;align-items:center;gap:16px">'
        '<div style="display:flex;align-items:center;gap:6px">'
        '<span style="font-size:0.82rem;color:#444;white-space:nowrap">Filter pts</span>'
        '<div style="width:60px">{filter_points}</div></div>'
        '<div style="display:flex;align-items:center;gap:6px">'
        '<span style="font-size:0.82rem;color:#444;white-space:nowrap">Filter method</span>{method}</div>'
        '</div>'
    )
    filter_form = _filter_tpl.batch(
        filter_points=mo.ui.text(value="25"),
        method=mo.ui.dropdown(
            options={"VBA-exact (slow)": "vba", "Fast (approximate)": "fast"},
            value="VBA-exact (slow)",
        ),
    ).form(submit_button_label="Filter", bordered=False)
    return (filter_form,)


@app.cell
def _(mo):
    _eval_tpl = mo.Html(
        '<div style="display:flex;align-items:center;gap:16px">'
        '<div style="display:flex;align-items:center;gap:6px">'
        '<span style="font-size:0.82rem;color:#444;white-space:nowrap">Static %</span>'
        '<div style="width:60px">{static_range}</div></div>'
        '<div style="display:flex;align-items:center;gap:6px">'
        '<span style="font-size:0.82rem;color:#444;white-space:nowrap">Dyn min %</span>'
        '<div style="width:60px">{dyn_min}</div></div>'
        '<div style="display:flex;align-items:center;gap:6px">'
        '<span style="font-size:0.82rem;color:#444;white-space:nowrap">Dyn max %</span>'
        '<div style="width:60px">{dyn_max}</div></div>'
        '</div>'
    )
    eval_form = _eval_tpl.batch(
        static_range=mo.ui.text(value="10.0"),
        dyn_min=mo.ui.text(value="20.0"),
        dyn_max=mo.ui.text(value="80.0"),
    ).form(submit_button_label="Evaluate", bordered=False)
    return (eval_form,)


# ── Data pipeline ──────────────────────────────────────────────────────────
@app.cell
def _(data_loader, file_upload, mo, raw_data_form):
    df_raw  = None
    step_df = None
    load_msg = mo.callout(mo.md("Set the row numbers, then click **Calculate**."), kind="info")

    _p = raw_data_form.value
    _file_given = bool(file_upload.value)
    _params_given = _p is not None
    _start_row_given = _params_given and int(_p["start_main_row"]) > 0
    if _file_given and _params_given and _start_row_given:
        try:
            _raw = file_upload.value[0].contents.decode("latin-1")
            df_raw, step_df = data_loader.parse_main_and_step_data(_raw, _p)

            load_msg = mo.callout(
                mo.md(f"**{file_upload.value[0].name}** — {len(df_raw):,} rows, {len(df_raw.columns)} columns: `{list(df_raw.columns)}`"),
                kind="success",
            )
        except Exception as _e:
            load_msg = mo.callout(mo.md(f"**Error:** {_e}"), kind="danger")
    return df_raw, load_msg, step_df


@app.cell
def _(cof_calc, df_raw, get_offset, mo, raw_data_form, step_df, utility_functions):
    df_display = None
    display_msg = None
    if df_raw is not None:
        try:
            _p = raw_data_form.value
            _cols = df_raw.columns
            _rename = {}
            _col_time  = int(_p["col_time"])
            _col_left  = int(_p["col_left"])
            _col_right = int(_p["col_right"])
            _col_load  = int(_p["col_load"])
            # col_* are 1-indexed column numbers as entered by the user; -1
            # converts to a 0-indexed position into df_raw.columns.
            if _col_time > 0:
                _rename[_cols[_col_time - 1]] = "Zeit"
            if _col_left > 0:
                _rename[_cols[_col_left - 1]] = "RK OFT Links"
            if _col_right > 0:
                _rename[_cols[_col_right - 1]] = "RK OFT Rechts"
            if _col_load > 0:
                _rename[_cols[_col_load - 1]] = "Belastung"
            df_display = df_raw.rename(columns=_rename).copy()
            if _p["nlc"]:
                _nlc = float(_p["nlc"])
            else:
                _nlc = None
            df_display = cof_calc.calculate(df_display, _nlc)
            df_display["CoF"] = df_display["CoF"].round(5)
            if step_df is not None:
                df_display = utility_functions.trim(
                    df_display,
                    float(step_df["Startzeit [s]"].min()),
                    round(float(step_df["Endzeit [s]"].max())),
                )
            if get_offset():
                df_display = utility_functions.offset(df_display)
        except Exception as _e:
            df_display = None
            display_msg = mo.callout(mo.md(f"**CoF Error:** {_e}"), kind="danger")
    return df_display, display_msg


@app.cell
def _(df_display, filter_form, mo, utility_functions):
    if df_display is not None:
        df_proc = df_display.copy()
    else:
        df_proc = None
    _fparams = filter_form.value
    if df_display is not None and _fparams is not None:
        try:
            _w = int(_fparams["filter_points"])
            _method = _fparams.get("method", "vba")
            if _w > 1:
                df_proc = utility_functions.filter(df_display.copy(), _w, method=_method)
        except Exception as _e:
            mo.output.append(mo.callout(mo.md(f"**Filter error:** {_e}"), kind="danger"))
    return (df_proc,)


@app.cell
def _(cof_calc, df_display, df_proc, eval_form, mo):
    cof_eval = None
    eval_msg = None
    _params = eval_form.value
    _have_filtered_data = df_proc is not None
    _have_display_data = df_display is not None
    _have_eval_params = _params is not None
    if _have_filtered_data and _have_display_data and _have_eval_params:
        try:
            _minima = cof_calc.find_minima(df_proc)
            _cof_res = cof_calc.get_static_and_dynamic_cof(
                df_display, _minima,
                float(_params["static_range"]), float(_params["dyn_min"]), float(_params["dyn_max"]),
            )
            cof_eval = {"minima": _minima, "cof_res": _cof_res}
        except Exception as _e:
            eval_msg = mo.callout(mo.md(f"**Evaluate error:** {_e}"), kind="danger")
    return cof_eval, eval_msg


@app.cell
def _(cof_eval, df_display, pd, stat_funcs, step_df):
    stats_result = None
    stats_error = None
    if cof_eval is not None and df_display is not None:
        try:
            if step_df is not None:
                _sdf = step_df
            else:
                _sdf = pd.DataFrame({
                    "Startzeit [s]": [df_display["Zeit"].min()],
                    "Endzeit [s]":   [df_display["Zeit"].max()],
                    "inactive":      [False],
                })
            stats_result = stat_funcs.CoF_Stat(cof_eval["cof_res"], _sdf)
        except Exception as _e:
            stats_error = str(_e)
    return stats_error, stats_result


# ── DB save ────────────────────────────────────────────────────────────────
@app.cell
def _(
    cof_eval,
    db_mod,
    df_display,
    df_proc,
    eval_form,
    file_upload,
    filter_form,
    mo,
    overwrite_btn,
    save_form,
    stats_result,
):
    save_msg = mo.Html('')
    _save_form_submitted = save_form.value is not None
    _have_eval_results = cof_eval is not None and stats_result is not None
    _have_file_and_data = bool(file_upload.value) and df_display is not None
    if _save_form_submitted and _have_eval_results and _have_file_and_data:
        _fname = file_upload.value[0].name
        _fparams = filter_form.value
        _eparams = eval_form.value
        _existing = db_mod.find_existing_test(_fname)
        if _existing is not None and not overwrite_btn.value:
            save_msg = mo.vstack([
                mo.callout(
                    mo.md(
                        f"A test named **{_fname}** (saved {_existing.uploaded_at}) "
                        "already exists."
                    ),
                    kind="warn",
                ),
                overwrite_btn,
            ], gap=1)
        else:
            try:
                if _existing is not None:
                    db_mod.delete_test(_existing.id)
                _fparams_given = _fparams is not None
                _filter_points_set = _fparams_given and int(_fparams.get("filter_points", 1)) > 1
                _filter_active = _filter_points_set and df_proc is not None
                _raw_df = df_display[["Zeit", "CoF"]].copy()
                if _filter_active:
                    _raw_df["Filtered CoF"] = df_proc["CoF"].values
                if _fparams:
                    _filter_window = int(_fparams["filter_points"])
                else:
                    _filter_window = None
                _test_id = db_mod.save_evaluation(
                    file_name=_fname,
                    data_type="OFT",
                    filter_window=_filter_window,
                    static_range=float(_eparams["static_range"]),
                    dynamic_min=float(_eparams["dyn_min"]),
                    dynamic_max=float(_eparams["dyn_max"]),
                    stats_df=stats_result,
                    per_cycle_df=cof_eval["cof_res"],
                    raw_df=_raw_df,
                    minima_df=cof_eval["minima"],
                )
                save_msg = mo.callout(mo.md(f"Saved as test **#{_test_id}**."), kind="success")
            except Exception as _e:
                save_msg = mo.callout(mo.md(f"**Save failed:** {_e}"), kind="danger")
    return (save_msg,)


# ── History panel ──────────────────────────────────────────────────────────
@app.cell
def _(mo):
    refresh_btn = mo.ui.run_button(label="🔄 Refresh")
    delete_btn = mo.ui.run_button(label="🗑 Delete selected", kind="danger")
    return delete_btn, refresh_btn


@app.cell
def _(db_mod, delete_btn, mo, pd, refresh_btn):
    # Reference these so marimo tracks them as real dependencies (reactivity
    # is derived from names actually used in the body, not the signature) —
    # this is what makes Refresh/Delete actually re-query the database.
    refresh_btn.value
    delete_btn.value

    _tests = db_mod.list_tests()
    if _tests:
        history_df = pd.DataFrame(_tests)
    else:
        history_df = pd.DataFrame(
            columns=["id", "file_name", "data_type", "uploaded_at", "filter_window",
                     "static_range", "dynamic_min", "dynamic_max",
                     "static_mean_cof", "dynamic_mean_cof", "steps"]
        )
    history_table = mo.ui.table(
        history_df, selection="single",
        pagination=True, show_column_summaries=False, show_data_types=False,
    )
    return (history_table,)


@app.cell
def _(delete_btn, db_mod, history_table, mo):
    delete_msg = mo.Html('')
    if delete_btn.value:
        _sel = history_table.value
        if _sel is not None and len(_sel) > 0:
            _id = int(_sel.iloc[0]["id"])
            if db_mod.delete_test(_id):
                delete_msg = mo.callout(mo.md(f"Deleted test **#{_id}**. Click Refresh to update the list."), kind="success")
            else:
                delete_msg = mo.callout(mo.md(f"Test #{_id} not found."), kind="warn")
        else:
            delete_msg = mo.callout(mo.md("Select a row first."), kind="warn")
    return (delete_msg,)


@app.cell
def _(db_mod, history_table, mo):
    _sel = history_table.value
    if _sel is not None and len(_sel) > 0:
        _test_id = int(_sel.iloc[0]["id"])
        _full = db_mod.get_full_table(_test_id)
        if not _full.empty:
            cycles_panel = mo.ui.table(_full, pagination=True,
                                        show_column_summaries=False, show_data_types=False)
        else:
            cycles_panel = mo.callout(mo.md("No saved data for this test."), kind="info")
    else:
        cycles_panel = mo.callout(mo.md("Select a row above to see the full CoF Analysis table for that test."), kind="info")
    return (cycles_panel,)


# ── Charts ─────────────────────────────────────────────────────────────────
@app.cell
def _(go):
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
    return add_cof_marker_trace, COF_MARKER_STYLES


@app.cell
def _(add_cof_marker_trace, db_mod, go, history_table, mo):
    _sel = history_table.value
    if _sel is None or len(_sel) == 0:
        history_chart = mo.Html(
            '<div style="height:360px;display:flex;align-items:center;justify-content:center;'
            'background:#fafafa;border-radius:6px;color:#bbb;font-size:13px">'
            "Select a saved test above to see its chart</div>"
        )
    else:
        _test_id = int(_sel.iloc[0]["id"])
        _full = db_mod.get_full_table(_test_id)
        if _full.empty or "Time [s]" not in _full.columns:
            history_chart = mo.callout(mo.md("No raw signal saved for this test."), kind="info")
        else:
            _fig = go.Figure()
            _fig.add_trace(go.Scattergl(
                x=_full["Time [s]"], y=_full["CoF"],
                mode="lines", name="CoF",
                line=dict(color="#2980b9", width=2),
            ))
            if "Filtered CoF" in _full.columns:
                _fig.add_trace(go.Scattergl(
                    x=_full["Time [s]"], y=_full["Filtered CoF"],
                    mode="lines", name="Filtered CoF",
                    line=dict(color="#e67e22", width=1.5),
                ))
            _zc = _full["Min time [s]"].dropna()
            add_cof_marker_trace(_fig, _zc, [0] * len(_zc), "zero_crossing", "Zero crossings")
            _s = _full[["Static CoF time [s]", "Static CoF"]].dropna()
            add_cof_marker_trace(_fig, _s["Static CoF time [s]"], _s["Static CoF"], "static", "Static CoF")
            _d = _full[["Dynamic CoF time [s]", "Dynamic CoF"]].dropna()
            add_cof_marker_trace(_fig, _d["Dynamic CoF time [s]"], _d["Dynamic CoF"], "dynamic", "Dynamic CoF")
            _ds = _full[["Dynamic start time [s]", "Dynamic start CoF"]].dropna()
            add_cof_marker_trace(_fig, _ds["Dynamic start time [s]"], _ds["Dynamic start CoF"], "dynamic_start", "Dynamic start")
            _de = _full[["Dynamic end time [s]", "Dynamic end CoF"]].dropna()
            add_cof_marker_trace(_fig, _de["Dynamic end time [s]"], _de["Dynamic end CoF"], "dynamic_end", "Dynamic end")
            _fig.update_layout(
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
            history_chart = mo.ui.plotly(
                _fig, config={"scrollZoom": True, "displayModeBar": True}
            )
    return (history_chart,)


@app.cell
def _(add_cof_marker_trace, cof_eval, df_display, df_proc, filter_form, go, mo, step_df, table_helpers):
    import io as _io, re as _re, json as _json

    # A long test can be 100,000+ raw samples, and a chart only a few hundred
    # pixels wide can't show more detail than that anyway — plotting every
    # raw point just makes panning/zooming slow with no visual benefit.
    # decimate_min_max keeps the curve's shape (spikes included) while
    # capping how many points the browser actually has to draw.
    _CHART_MAX_POINTS = 12000

    if df_display is None:
        cof_chart = mo.Html(
            '<div style="height:360px;display:flex;align-items:center;justify-content:center;'
            'background:#fafafa;border-radius:6px;color:#bbb;font-size:13px">'
            "Upload a file to see the chart</div>"
        )
    else:
        # ── A: data prep ─────────────────────────────────────────────────────
        _fparams = filter_form.value
        _fparams_given = _fparams is not None
        _filter_points_set = _fparams_given and int(_fparams.get("filter_points", 1)) > 1
        _filter_active = _filter_points_set and df_proc is not None

        # ── B: build figure ───────────────────────────────────────────────────
        _fig = go.Figure()

        if _filter_active:
            _cof_line_color = "rgba(41,128,185,0.35)"
        else:
            _cof_line_color = "#2980b9"

        # Line traces — Scattergl uses WebGL: handles large datasets efficiently in the browser
        _cof_x, _cof_y = table_helpers.decimate_min_max(
            df_display["Zeit"], df_display["CoF"], _CHART_MAX_POINTS
        )
        _fig.add_trace(go.Scattergl(
            x=_cof_x, y=_cof_y,
            mode="lines", name="CoF",
            line=dict(color=_cof_line_color, width=2),
        ))
        if _filter_active:
            _filtered_x, _filtered_y = table_helpers.decimate_min_max(
                df_proc["Zeit"], df_proc["CoF"], _CHART_MAX_POINTS
            )
            _fig.add_trace(go.Scattergl(
                x=_filtered_x, y=_filtered_y,
                mode="lines", name="Filtered CoF",
                line=dict(color="#e67e22", width=1.5),
            ))

        # Evaluation markers — Scattergl, but always a small number of points
        # (a few hundred at most, one per detected cycle) so decimation is
        # not needed here — only the raw-sample line traces above are big
        # enough to matter.
        if cof_eval is not None:
            _mn = cof_eval["minima"]
            _cr = cof_eval["cof_res"]
            add_cof_marker_trace(_fig, _mn["Min Zeit"], [0] * len(_mn), "zero_crossing", "Zero crossings")
            add_cof_marker_trace(_fig, _cr["staticCoFTime"], _cr["staticCoF"], "static", "Static CoF")
            add_cof_marker_trace(_fig, _cr["dynamicCoFTime"], _cr["dynamicCoF"], "dynamic", "Dynamic CoF")
            add_cof_marker_trace(_fig, _cr["startdynamicTime"], _cr["startdynamicCoF"], "dynamic_start", "Dynamic start")
            add_cof_marker_trace(_fig, _cr["enddynamicTime"], _cr["enddynamicCoF"], "dynamic_end", "Dynamic end")

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
        if _m:
            _cdn = _m.group(1)
        else:
            _cdn = "https://cdn.plot.ly/plotly-latest.min.js"

        _fig_dict = _json.loads(_fig.to_json())
        _d = _json.dumps(_fig_dict["data"])
        _l = _json.dumps(_fig_dict["layout"])

        # srcdoc iframe: scripts execute, same origin as parent so window.parent is accessible.
        # __cofXR on the parent window stores the x-axis zoom range across cell re-renders.
        #
        # The Y-axis is fixedrange (locked against manual drag/scroll) but is NOT left on
        # plain autorange, because autorange fits the whole file at once — zooming into a
        # narrow time window then leaves the curve looking flat, squashed against a Y-scale
        # sized for the entire dataset. fitYRange() below recomputes a Y range from just the
        # points inside the currently-visible X window (skipping inf/-inf/NaN, since a single
        # divide-by-near-zero sample elsewhere in the file would otherwise blow out the scale)
        # every time the X range changes, so the curve always fills the visible plot area.
        _iframe_html = f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<style>body{{margin:0;overflow:hidden}}</style>
<script src="{_cdn}"></script>
</head><body>
<div id="c" style="width:100vw;height:420px"></div>
<script>
var d={_d}, l={_l};

// Plotly.py packs large numeric arrays into a compact typed-array form —
// {{"dtype": "f8", "bdata": "<base64>"}} — instead of a plain JS array, to
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

// Decode every trace's x/y ONCE here, up front — not inside fitYRange. A real
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

        _srcdoc = _iframe_html.replace("&", "&amp;").replace("<", "&lt;").replace("'", "&#39;")
        cof_chart = mo.Html(
            f"<iframe srcdoc='{_srcdoc}' style='width:100%;height:440px;border:none;display:block'></iframe>"
        )
    return (cof_chart,)


# ── Results table ──────────────────────────────────────────────────────────
@app.cell
def _(cof_eval, df_display, df_proc, filter_form, mo, pd, stats_error, stats_result, table_helpers):
    import numpy as _np

    if df_display is None:
        results_panel = mo.Html(
            '<div style="height:60px;display:flex;align-items:center;justify-content:center;'
            'color:#bbb;font-size:13px">Click Calculate to see results</div>'
        )
    else:
        # Column-specific rounding precision below has no known rationale beyond
        # matching the reference VBA tool's output column-by-column; preserved
        # as-is rather than unified to a single value.
        _DEFAULT_COF_DECIMALS = 15
        _MINUS_MIN_COF_DECIMALS = 16
        _PLUS_MIN_COF_DECIMALS = 18

        _N = len(df_display)
        _fparams = filter_form.value
        _fparams_given = _fparams is not None
        _filter_points_set = _fparams_given and int(_fparams.get("filter_points", 1)) > 1
        _filter_active = _filter_points_set and df_proc is not None

        def _pad_column(arr):
            return table_helpers.pad(arr, _N)

        def _round_and_pad_column(arr, decimals=_DEFAULT_COF_DECIMALS):
            return table_helpers.round_and_pad(arr, _N, decimals)

        # ── Always present (after Calculate) ─────────────────────────────────
        _cols = {
            "Time [s]":    list(df_display["Zeit"]),
            "CoF":         list(df_display["CoF"].round(_DEFAULT_COF_DECIMALS)),
        }

        # ── Added after Filter ────────────────────────────────────────────────
        if _filter_active:
            _cols["Filtered CoF"] = list(df_proc["CoF"].round(_DEFAULT_COF_DECIMALS))

        # ── Added after Evaluate ──────────────────────────────────────────────
        if cof_eval is not None:
            if stats_error is not None:
                _error_column = [stats_error]
                for _i in range(_N - 1):
                    _error_column.append(_np.nan)
                _cols["Eval error"] = _error_column
            else:
                try:
                    _stats = stats_result
                    _cr = cof_eval["cof_res"]
                    _mn = cof_eval["minima"]
                    _cols["Static CoF time [s]"] = _pad_column(_cr["staticCoFTime"])
                    _cols["Static CoF"] = _round_and_pad_column(_cr["staticCoF"])
                    _cols["Dynamic CoF time [s]"] = _pad_column(_cr["dynamicCoFTime"])
                    _cols["Dynamic CoF"] = _round_and_pad_column(_cr["dynamicCoF"])
                    _cols["Dynamic std dev"] = _round_and_pad_column(_cr["dynamicCoFSD"])
                    _cols["Dynamic N"] = _pad_column(_cr["dynamicCoFn"])
                    _cols["Dynamic CoF sum"] = _round_and_pad_column(_cr["dynamicCoFsigma"])
                    _cols["Dynamic CoF variance"] = _round_and_pad_column(_cr["dynamicCoFvariance"])
                    _cols["Time range [s]"] = _pad_column(_stats["Time Range"])
                    _cols["Static mean CoF"] = _round_and_pad_column(_stats["Static Avg"])
                    _cols["Static std dev"] = _round_and_pad_column(_stats["Static Std Dev"])
                    _cols["Static N"] = _pad_column(_stats["Static N"])
                    _cols["Static CoF sum"] = _round_and_pad_column(_stats["Static Avg x N"])
                    _cols["Static CoF variance"] = _round_and_pad_column(_stats["Static Var"])
                    _cols["Dynamic mean CoF"] = _round_and_pad_column(_stats["Dynamic Avg"])
                    _cols["Dynamic mean std dev"] = _round_and_pad_column(_stats["Dynamic Std Dev"])
                    _cols["Dynamic mean N"] = _pad_column(_stats["Dynamic N"])
                    _cols["Dynamic CoF avg×N"] = _round_and_pad_column(_stats["Dynamic Avg x N"])
                    _cols["Dynamic CoF var (step)"] = _round_and_pad_column(_stats["Dynamic Var"])
                    _cols["-Min time [s]"] = _pad_column(_mn["-Min Zeit"])
                    _cols["-Min CoF"] = _round_and_pad_column(_mn["-Min CoF"], _MINUS_MIN_COF_DECIMALS)
                    _cols["+Min time [s]"] = _pad_column(_mn["+Min Zeit"])
                    _cols["+Min CoF"] = _round_and_pad_column(_mn["+Min CoF"], _PLUS_MIN_COF_DECIMALS)
                    _cols["Min time [s]"] = _pad_column(_mn["Min Zeit"])
                    _cols["CoF minima"] = _round_and_pad_column(_mn["Min CoF"])
                    _cols["Dynamic start time [s]"] = _pad_column(_cr["startdynamicTime"])
                    _cols["Dynamic start CoF"] = _round_and_pad_column(_cr["startdynamicCoF"])
                    _cols["Dynamic end time [s]"] = _pad_column(_cr["enddynamicTime"])
                    _cols["Dynamic end CoF"] = _round_and_pad_column(_cr["enddynamicCoF"])
                except Exception as _e:
                    _error_column = [str(_e)]
                    for _i in range(_N - 1):
                        _error_column.append(_np.nan)
                    _cols["Eval error"] = _error_column

        try:
            results_panel = mo.vstack([
                mo.Html('<p class="panel-title">Results</p>'),
                mo.ui.table(
                    pd.DataFrame(_cols),
                    pagination=True,
                    show_column_summaries=False,
                    show_data_types=False,
                ),
            ], gap=1)
        except Exception as _e:
            results_panel = mo.callout(mo.md(f"Results error: {_e}"), kind="warn")
    return (results_panel,)


# ── Final layout ───────────────────────────────────────────────────────────
@app.cell
def _(data_loader, display_msg, file_upload, load_msg, mo, raw_data_form):
    if file_upload.value:
        _rvm_test = file_upload.value[0].name.replace(".txt", "")
    else:
        _rvm_test = "—"

    if file_upload.value:
        _raw = file_upload.value[0].contents.decode("latin-1")
        _df_file = data_loader.parse_preview_table(_raw)
        _total = len(_df_file)
        _justify = {}
        for _col in _df_file.columns:
            _justify[_col] = "left"
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

    if display_msg is not None:
        _display_msg_html = display_msg
    else:
        _display_msg_html = mo.Html('')

    rawdata_tab = mo.vstack([
        mo.hstack([file_upload], justify="start"),
        mo.Html('<hr class="divider">'),
        mo.Html(f'<div style="display:flex;flex-direction:column;gap:2px">'
                f'<span style="font-size:0.6rem;color:#999;font-weight:700;letter-spacing:1px">RVM TEST</span>'
                f'<span style="font-size:0.9rem;font-weight:600;color:#1f2a40">{_rvm_test}</span></div>'),
        mo.Html('<hr class="divider">'),
        raw_data_form,
        mo.Html('<hr class="divider">'),
        load_msg,
        _display_msg_html,
        _raw_table,
    ], gap=2)
    return (rawdata_tab,)


@app.cell
def _(cof_chart, display_msg, eval_form, eval_msg, filter_form, mo, offset_form, results_panel, save_form, save_msg):
    if display_msg is not None:
        _display_msg_html = display_msg
    else:
        _display_msg_html = mo.Html('')

    if eval_msg is not None:
        _eval_msg_html = eval_msg
    else:
        _eval_msg_html = mo.Html('')

    analysis_tab = mo.vstack([
        mo.hstack([
            mo.vstack([mo.Html('<p class="section-label" style="margin:0">ACTIONS</p>'), offset_form], gap=1),
            mo.Html('<div style="width:1px;background:#eee;align-self:stretch"></div>'),
            mo.vstack([mo.Html('<p class="section-label" style="margin:0">FILTER</p>'), filter_form], gap=1),
            mo.Html('<div style="width:1px;background:#eee;align-self:stretch"></div>'),
            mo.vstack([mo.Html('<p class="section-label" style="margin:0">EVALUATE</p>'), eval_form], gap=1),
            mo.Html('<div style="width:1px;background:#eee;align-self:stretch"></div>'),
            mo.vstack([mo.Html('<p class="section-label" style="margin:0">SAVE</p>'), save_form], gap=1),
        ], gap=3, align="start"),
        save_msg,
        mo.Html('<hr class="divider">'),
        mo.vstack([
            mo.Html('<p class="panel-title">Analysis Visualization</p>'),
            _display_msg_html,
            _eval_msg_html,
            cof_chart,
            mo.Html('<hr class="divider">'),
            results_panel,
        ], gap=1),
    ], gap=2)
    return (analysis_tab,)


@app.cell
def _(cycles_panel, delete_btn, delete_msg, history_chart, history_table, mo, refresh_btn):
    history_tab = mo.vstack([
        mo.hstack([refresh_btn, delete_btn], gap=2, justify="start"),
        delete_msg,
        mo.Html('<hr class="divider">'),
        mo.Html('<p class="panel-title">Saved Tests</p>'),
        history_table,
        mo.Html('<hr class="divider">'),
        mo.Html('<p class="panel-title">Chart</p>'),
        history_chart,
        mo.Html('<hr class="divider">'),
        mo.Html('<p class="panel-title">Results</p>'),
        cycles_panel,
    ], gap=2)
    return (history_tab,)


@app.cell
def _(analysis_tab, history_tab, mo, rawdata_tab):
    _navbar = mo.Html("""
    <div class="navbar">
      <div><span class="navbar-title">FRICTION EVALUATION</span><span class="navbar-version">v2.0</span></div>
      <span class="navbar-user">Marimo</span>
    </div>
    """)

    mo.vstack([
        _navbar,
        mo.ui.tabs({
            "📋  Raw Data":      rawdata_tab,
            "📊  CoF Analysis":  analysis_tab,
            "🗂  History":       history_tab,
        }),
    ], gap=0)
    return


if __name__ == "__main__":
    app.run()
