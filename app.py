import marimo

__generated_with = "0.23.9"
app = marimo.App(width="full")


# ── Imports ──────────────────────────────────────────────────────────────────
@app.cell
def _():
    import marimo as mo
    import sys, os

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

    import data_loader
    import pipeline
    import charts
    import results_table
    import table_helpers

    return charts, data_loader, mo, pipeline, results_table, table_helpers


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
      body { background: #eef1f4; }
      .navbar {
        background: #1f2a40; padding: 0 24px; height: 50px;
        display: flex; align-items: center; justify-content: space-between;
        border-radius: 8px 8px 0 0;
      }
      .navbar-title { color: #4cceac; font-weight: 700; font-size: 1rem; letter-spacing: 0.5px; }
      .navbar-version { color: #fff; font-size: 0.75rem; margin-left: 10px; }
      .navbar-user { color: #aaa; font-size: 0.8rem; }
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

    # A shared inline style (not a CSS class) for wrapping composites that
    # contain real interactive widgets (forms, buttons) - mo.Html can't wrap
    # a live widget tree in a literal HTML string without losing its
    # interactivity, so card styling for those has to go through
    # Html.style() on the vstack/hstack itself instead of a CSS class.
    PANEL_STYLE = {
        "background": "#fff",
        "border-radius": "8px",
        "padding": "16px",
        "box-shadow": "0 1px 4px rgba(0,0,0,0.08)",
    }
    # Same card look, but as a fixed-height flex column with the button
    # pinned to the bottom - so the 4 action cards (Actions/Filter/
    # Evaluate/Save) line their buttons up on one baseline regardless of
    # how many fields the middle of each card has.
    ACTION_CARD_STYLE = {
        "background": "#fff",
        "border-radius": "8px",
        "padding": "16px",
        "box-shadow": "0 1px 4px rgba(0,0,0,0.08)",
        "display": "flex",
        "flex-direction": "column",
        "justify-content": "space-between",
        "min-height": "110px",
    }
    return ACTION_CARD_STYLE, PANEL_STYLE


# ── App state ──────────────────────────────────────────────────────────────
@app.cell
def _(mo):
    get_offset, set_offset = mo.state(False)
    return get_offset, set_offset


@app.cell
def _(mo):
    # Holds the last successfully parsed (df_raw, step_df, params), so
    # editing a field doesn't blank out the result until Calculate is
    # actually clicked again.
    get_parsed_data, set_parsed_data = mo.state(None)
    return get_parsed_data, set_parsed_data


@app.cell
def _(mo):
    # One shared status message per tab, each shown in a single place on
    # that tab's page. Whichever action on that tab last had something to
    # say calls its set_..._status_msg() to replace it - so each tab has
    # exactly one message box, always showing that tab's own latest action,
    # instead of every action having its own separate, independently-timed
    # message box scattered around the page. Kept as two separate states
    # (not one shared one) so an action on the Analysis tab never overwrites
    # what's showing on the History tab, or vice versa.
    get_results_status_msg, set_results_status_msg = mo.state(
        mo.callout(mo.md("Set the row numbers, then click **Calculate**."), kind="info")
    )
    return get_results_status_msg, set_results_status_msg


@app.cell
def _(mo):
    get_history_status_msg, set_history_status_msg = mo.state(mo.Html(''))
    return get_history_status_msg, set_history_status_msg


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
def _(mo):
    # Kept outside the form (live, not submit-only) so unchecking it can
    # grey out the step fields below right away, without needing "Calculate".
    has_step_checkbox = mo.ui.checkbox(label="Has step data", value=True)
    return (has_step_checkbox,)


@app.cell
def _(mo):
    # A separate button (not a form's built-in submit button) so it can be
    # placed anywhere in the layout, independent of the fields.
    calculate_button = mo.ui.run_button(label="Calculate")
    return (calculate_button,)


@app.cell
def _(mo):
    open_excel_btn = mo.ui.run_button(label="📂 Open in Excel")
    return (open_excel_btn,)


@app.cell
def _(mo):
    open_results_excel_btn = mo.ui.run_button(label="📂 Open Results in Excel")
    return (open_results_excel_btn,)


@app.cell
def _(data_loader, file_upload, mo, open_excel_btn, set_results_status_msg):
    if open_excel_btn.value:
        if file_upload.value:
            _raw = file_upload.value[0].contents.decode("latin-1")
            try:
                data_loader.open_in_excel(_raw, file_upload.value[0].name)
                set_results_status_msg(mo.callout(mo.md("Opened in Excel."), kind="success"))
            except Exception as _e:
                set_results_status_msg(mo.callout(mo.md(f"**Could not open Excel:** {_e}"), kind="danger"))
        else:
            set_results_status_msg(mo.callout(mo.md("Upload a file first."), kind="warn"))
    return


@app.cell
def _(file_upload, has_step_checkbox, mo):
    _step_fields_disabled = not has_step_checkbox.value
    if file_upload.value:
        _total = len(file_upload.value[0].contents.decode("latin-1").splitlines())
    else:
        _total = 0
    # Inline styles throughout, not CSS classes: a page-level <style> rule
    # can style plain elements like <hr>/<p> fine (see .divider,
    # .section-label elsewhere), but a label sitting in the same flex row as
    # a marimo widget needs an explicit inline min-width to reliably line up
    # - same reasoning as the width:60px wrapper already used for
    # Filter/Evaluate's inputs below.
    _row = '<div style="display:flex;align-items:center;gap:8px">' \
           '<span style="font-size:0.82rem;color:#444;min-width:160px;flex-shrink:0">{label}</span>{{{field}}}</div>'
    _grid_open = '<div style="display:grid;grid-template-columns:repeat(2, minmax(240px, 1fr));gap:10px 32px">'
    _grid_close = '</div>'

    _raw_data_tpl = mo.Html(
        '<div style="display:flex;flex-direction:column;gap:14px">'
        + _row.format(label="Normal Load Correction", field="nlc")
        + '<hr class="divider">'
        '<p class="section-label" style="margin:0">STEP DATA</p>'
        + _grid_open
        + _row.format(label="Start Step", field="start_step_row")
        + _row.format(label="End Step", field="end_step_row")
        + _row.format(label="Step Time col #", field="step_col_time")
        + _grid_close
        + '<hr class="divider">'
        '<p class="section-label" style="margin:0">MAIN DATA</p>'
        + _grid_open
        + _row.format(label="Start Main Data", field="start_main_row")
        + _row.format(label="Stop Main Data", field="stop_main_row")
        + _row.format(label="Time col #", field="col_time")
        + _row.format(label="Friction Left col #", field="col_left")
        + _row.format(label="Friction Right col #", field="col_right")
        + _row.format(label="Normal Load col #", field="col_load")
        + _grid_close
        + '</div>'
    )
    raw_data_form = _raw_data_tpl.batch(
        nlc=mo.ui.text(value=""),
        start_step_row=mo.ui.text(value="0", disabled=_step_fields_disabled),
        end_step_row=mo.ui.text(value="0", disabled=_step_fields_disabled),
        step_col_time=mo.ui.text(value="1", disabled=_step_fields_disabled),
        start_main_row=mo.ui.text(value="41"),
        stop_main_row=mo.ui.text(value=str(_total)),
        col_time=mo.ui.text(value="1"),
        col_left=mo.ui.text(value="13"),
        col_right=mo.ui.text(value="14"),
        col_load=mo.ui.text(value="3"),
    )
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
def _(
    calculate_button,
    data_loader,
    file_upload,
    get_parsed_data,
    has_step_checkbox,
    mo,
    raw_data_form,
    set_parsed_data,
    set_results_status_msg,
):
    # raw_data_form's fields are live now (not a submit-gated form), so this
    # cell re-runs on every keystroke too - but it only re-parses the file
    # when Calculate was actually clicked. Otherwise it just re-reads the
    # last computed result from state, so editing a field doesn't blank out
    # the current result.
    if calculate_button.value:
        _p = raw_data_form.value
        if data_loader.is_ready_to_parse(bool(file_upload.value), _p):
            try:
                _raw = file_upload.value[0].contents.decode("latin-1")
                _p = dict(_p)
                _p["has_step"] = has_step_checkbox.value
                _df_raw, _step_df = data_loader.parse_main_and_step_data(_raw, _p)
                set_parsed_data((_df_raw, _step_df, _p))
                set_results_status_msg(mo.callout(
                    mo.md(f"**{file_upload.value[0].name}** — {len(_df_raw):,} rows, {len(_df_raw.columns)} columns: `{list(_df_raw.columns)}`"),
                    kind="success",
                ))
            except Exception as _e:
                set_parsed_data((None, None, None))
                set_results_status_msg(mo.callout(mo.md(f"**Error:** {_e}"), kind="danger"))

    _parsed = get_parsed_data()
    if _parsed is None:
        df_raw = None
        step_df = None
        committed_params = None
    else:
        df_raw, step_df, committed_params = _parsed
    return committed_params, df_raw, step_df


@app.cell
def _(committed_params, df_raw, get_offset, mo, pipeline, set_results_status_msg, step_df):
    df_display = None
    if df_raw is not None:
        try:
            # Use the params from the last Calculate click, not the fields'
            # current (possibly since-edited) live values - column choices
            # shouldn't take effect until Calculate is clicked either.
            df_display = pipeline.compute_display_df(df_raw, step_df, committed_params, get_offset())
        except Exception as _e:
            df_display = None
            set_results_status_msg(mo.callout(mo.md(f"**CoF Error:** {_e}"), kind="danger"))
    return (df_display,)


@app.cell
def _(df_display, filter_form, mo, pipeline, set_results_status_msg):
    if df_display is not None:
        try:
            df_proc = pipeline.compute_filtered_df(df_display, filter_form.value)
        except Exception as _e:
            df_proc = df_display.copy()
            set_results_status_msg(mo.callout(mo.md(f"**Filter error:** {_e}"), kind="danger"))
    else:
        df_proc = None
    return (df_proc,)


@app.cell
def _(df_display, df_proc, eval_form, mo, pipeline, set_results_status_msg):
    cof_eval = None
    try:
        cof_eval = pipeline.compute_evaluation(df_display, df_proc, eval_form.value)
    except Exception as _e:
        set_results_status_msg(mo.callout(mo.md(f"**Evaluate error:** {_e}"), kind="danger"))
    return (cof_eval,)


@app.cell
def _(cof_eval, df_display, pipeline, step_df):
    stats_result = None
    stats_error = None
    if cof_eval is not None and df_display is not None:
        try:
            stats_result = pipeline.compute_stats(cof_eval, df_display, step_df)
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
    pipeline,
    save_form,
    set_results_status_msg,
    stats_result,
):
    _save_form_submitted = save_form.value is not None
    _have_eval_results = cof_eval is not None and stats_result is not None
    _have_file_and_data = bool(file_upload.value) and df_display is not None
    if _save_form_submitted and _have_eval_results and _have_file_and_data:
        _fname = file_upload.value[0].name
        _fparams = filter_form.value
        _eparams = eval_form.value
        _existing = db_mod.find_existing_test(_fname)
        if _existing is not None and not overwrite_btn.value:
            set_results_status_msg(mo.vstack([
                mo.callout(
                    mo.md(
                        f"A test named **{_fname}** (saved {_existing.uploaded_at}) "
                        "already exists."
                    ),
                    kind="warn",
                ),
                overwrite_btn,
            ], gap=1))
        else:
            try:
                if _existing is not None:
                    db_mod.delete_test(_existing.id)
                _filter_active = pipeline.is_filter_active(_fparams, df_proc)
                _test_id = db_mod.save_full_evaluation(
                    _fname, _fparams, _eparams, df_display, df_proc, _filter_active, cof_eval, stats_result,
                )
                set_results_status_msg(mo.callout(mo.md(f"Saved as test **#{_test_id}**."), kind="success"))
            except Exception as _e:
                set_results_status_msg(mo.callout(mo.md(f"**Save failed:** {_e}"), kind="danger"))
    return


# ── History panel ──────────────────────────────────────────────────────────
@app.cell
def _(mo):
    refresh_btn = mo.ui.run_button(label="🔄 Refresh")
    delete_btn = mo.ui.run_button(label="🗑 Delete selected", kind="danger")
    open_history_excel_btn = mo.ui.run_button(label="📂 Open in Excel")
    return delete_btn, open_history_excel_btn, refresh_btn


@app.cell
def _(db_mod, delete_btn, mo, refresh_btn):
    # Reference these so marimo tracks them as real dependencies (reactivity
    # is derived from names actually used in the body, not the signature) —
    # this is what makes Refresh/Delete actually re-query the database.
    refresh_btn.value
    delete_btn.value

    history_df = db_mod.list_tests_df()
    history_table = mo.ui.table(
        history_df, selection="single",
        pagination=True, show_column_summaries=False, show_data_types=False,
    )
    return (history_table,)


@app.cell
def _(delete_btn, db_mod, history_table, mo, set_history_status_msg):
    if delete_btn.value:
        _sel = history_table.value
        if _sel is not None and len(_sel) > 0:
            _id = int(_sel.iloc[0]["id"])
            if db_mod.delete_test(_id):
                set_history_status_msg(mo.callout(mo.md(f"Deleted test **#{_id}**. Click Refresh to update the list."), kind="success"))
            else:
                set_history_status_msg(mo.callout(mo.md(f"Test #{_id} not found."), kind="warn"))
        else:
            set_history_status_msg(mo.callout(mo.md("Select a row first."), kind="warn"))
    return


@app.cell
def _(db_mod, history_table, mo, open_history_excel_btn):
    _sel = history_table.value
    if _sel is not None and len(_sel) > 0:
        _test_id = int(_sel.iloc[0]["id"])
        _n_raw = db_mod.count_raw_samples(_test_id)
        _n_eval = db_mod.count_cycles(_test_id)
        if _n_raw == 0 and _n_eval == 0:
            cycles_panel = mo.callout(mo.md("No saved data for this test."), kind="info")
        else:
            cycles_panel = mo.vstack([
                mo.Html(f'<p style="font-size:0.85rem;color:#444;margin:0 0 4px 0">{_n_raw:,} raw samples, {_n_eval:,} evaluated cycles.</p>'),
                open_history_excel_btn,
            ], gap=1)
    else:
        cycles_panel = mo.callout(mo.md("Select a row above to see the full CoF Analysis table for that test."), kind="info")
    return (cycles_panel,)


@app.cell
def _(data_loader, db_mod, history_table, mo, open_history_excel_btn, set_history_status_msg, table_helpers):
    if open_history_excel_btn.value:
        _sel = history_table.value
        if _sel is not None and len(_sel) > 0:
            _test_id = int(_sel.iloc[0]["id"])
            try:
                _raw_table = db_mod.get_full_raw_table(_test_id)
                _eval_table = db_mod.get_full_eval_table(_test_id)
                _combined = table_helpers.combine_padded(_raw_table, _eval_table)
                data_loader.open_dataframe_in_excel(_combined, f"test_{_test_id}_results")
                set_history_status_msg(mo.callout(mo.md("Opened in Excel."), kind="success"))
            except Exception as _e:
                set_history_status_msg(mo.callout(mo.md(f"**Could not open Excel:** {_e}"), kind="danger"))
        else:
            set_history_status_msg(mo.callout(mo.md("Select a saved test first."), kind="warn"))
    return


# ── Charts ─────────────────────────────────────────────────────────────────
@app.cell
def _(charts, db_mod, history_table, mo):
    _sel = history_table.value
    if _sel is None or len(_sel) == 0:
        history_chart = mo.Html(
            '<div style="height:360px;display:flex;align-items:center;justify-content:center;'
            'background:#fafafa;border-radius:6px;color:#bbb;font-size:13px">'
            "Select a saved test above to see its chart</div>"
        )
    else:
        _test_id = int(_sel.iloc[0]["id"])
        _raw_table = db_mod.get_full_raw_table(_test_id)
        _eval_table = db_mod.get_full_eval_table(_test_id)
        _fig = charts.build_history_figure(_raw_table, _eval_table)
        if _fig is None:
            history_chart = mo.callout(mo.md("No raw signal saved for this test."), kind="info")
        else:
            history_chart = mo.ui.plotly(_fig, config={"scrollZoom": True, "displayModeBar": True})
    return (history_chart,)


@app.cell
def _(charts, cof_eval, df_display, df_proc, filter_form, mo, pipeline, step_df):
    if df_display is None:
        cof_chart = mo.Html(
            '<div style="height:360px;display:flex;align-items:center;justify-content:center;'
            'background:#fafafa;border-radius:6px;color:#bbb;font-size:13px">'
            "Upload a file to see the chart</div>"
        )
    else:
        _filter_active = pipeline.is_filter_active(filter_form.value, df_proc)
        _fig = charts.build_cof_figure(df_display, df_proc, cof_eval, step_df, _filter_active)
        cof_chart = mo.Html(charts.figure_to_zoom_iframe_html(_fig))
    return (cof_chart,)


# ── Results table ──────────────────────────────────────────────────────────
@app.cell
def _(cof_eval, df_display, mo, open_results_excel_btn):
    if df_display is None:
        results_panel = mo.Html(
            '<div style="height:60px;display:flex;align-items:center;justify-content:center;'
            'color:#bbb;font-size:13px">Click Calculate to see results</div>'
        )
    else:
        _n_raw = len(df_display)
        if cof_eval is not None:
            _n_eval = len(cof_eval["cof_res"])
            _summary = f"{_n_raw:,} raw samples, {_n_eval:,} evaluated cycles."
        else:
            _summary = f"{_n_raw:,} raw samples."
        results_panel = mo.vstack([
            mo.Html('<p class="panel-title">Results</p>'),
            mo.Html(f'<p style="font-size:0.85rem;color:#444;margin:0 0 4px 0">{_summary}</p>'),
            open_results_excel_btn,
        ], gap=1)
    return (results_panel,)


@app.cell
def _(
    cof_eval,
    data_loader,
    df_display,
    df_proc,
    filter_form,
    mo,
    open_results_excel_btn,
    pipeline,
    results_table,
    set_results_status_msg,
    stats_error,
    stats_result,
    table_helpers,
):
    if open_results_excel_btn.value and df_display is not None:
        try:
            _filter_active = pipeline.is_filter_active(filter_form.value, df_proc)
            _df_raw_results = results_table.build_raw_table(df_display, df_proc, _filter_active)
            _df_eval_results = results_table.build_eval_table(cof_eval, stats_result, stats_error)
            if _df_eval_results is not None:
                _combined = table_helpers.combine_padded(_df_raw_results, _df_eval_results)
            else:
                _combined = _df_raw_results
            data_loader.open_dataframe_in_excel(_combined, "results")
            set_results_status_msg(mo.callout(mo.md("Opened results in Excel."), kind="success"))
        except Exception as _e:
            set_results_status_msg(mo.callout(mo.md(f"**Could not open Excel:** {_e}"), kind="danger"))
    return


# ── Final layout ───────────────────────────────────────────────────────────
@app.cell
def _(
    ACTION_CARD_STYLE,
    PANEL_STYLE,
    calculate_button,
    cof_chart,
    eval_form,
    file_upload,
    filter_form,
    get_results_status_msg,
    has_step_checkbox,
    mo,
    offset_form,
    open_excel_btn,
    raw_data_form,
    results_panel,
    save_form,
):
    if file_upload.value:
        _rvm_test = file_upload.value[0].name.replace(".txt", "")
    else:
        _rvm_test = "—"

    _upload_card = mo.vstack([
        mo.hstack([file_upload, open_excel_btn], justify="start", align="center"),
        get_results_status_msg(),
        mo.Html('<hr class="divider">'),
        mo.Html(f'<div style="display:flex;flex-direction:column;gap:2px">'
                f'<span style="font-size:0.6rem;color:#999;font-weight:700;letter-spacing:1px">RVM TEST</span>'
                f'<span style="font-size:0.9rem;font-weight:600;color:#1f2a40">{_rvm_test}</span></div>'),
    ], gap=1).style(PANEL_STYLE)

    _raw_data_card = mo.vstack([
        mo.Html('<p class="panel-title">Raw Data</p>'),
        has_step_checkbox,
        raw_data_form,
        mo.Html('<hr class="divider">'),
        calculate_button,
    ], gap=2).style(PANEL_STYLE)

    _actions_row = mo.hstack([
        mo.vstack([mo.Html('<p class="section-label" style="margin:0">ACTIONS</p>'), offset_form], gap=1, justify="space-between").style(ACTION_CARD_STYLE),
        mo.vstack([mo.Html('<p class="section-label" style="margin:0">FILTER</p>'), filter_form], gap=1, justify="space-between").style(ACTION_CARD_STYLE),
        mo.vstack([mo.Html('<p class="section-label" style="margin:0">EVALUATE</p>'), eval_form], gap=1, justify="space-between").style(ACTION_CARD_STYLE),
        mo.vstack([mo.Html('<p class="section-label" style="margin:0">SAVE</p>'), save_form], gap=1, justify="space-between").style(ACTION_CARD_STYLE),
    ], gap=2, align="stretch", widths="equal")

    _viz_card = mo.vstack([
        mo.Html('<p class="panel-title">Analysis Visualization</p>'),
        cof_chart,
        mo.Html('<hr class="divider">'),
        results_panel,
    ], gap=1).style(PANEL_STYLE)

    results_tab = mo.vstack([
        _upload_card,
        _raw_data_card,
        _actions_row,
        _viz_card,
    ], gap=2).style({"padding": "20px 0"})
    return (results_tab,)


@app.cell
def _(PANEL_STYLE, cycles_panel, delete_btn, get_history_status_msg, history_chart, history_table, mo, refresh_btn):
    _tests_card = mo.vstack([
        mo.hstack([refresh_btn, delete_btn], gap=2, justify="start"),
        get_history_status_msg(),
        mo.Html('<hr class="divider">'),
        mo.Html('<p class="panel-title">Saved Tests</p>'),
        history_table,
    ], gap=2).style(PANEL_STYLE)

    _chart_card = mo.vstack([
        mo.Html('<p class="panel-title">Chart</p>'),
        history_chart,
        mo.Html('<hr class="divider">'),
        cycles_panel,
    ], gap=1).style(PANEL_STYLE)

    history_tab = mo.vstack([
        _tests_card,
        _chart_card,
    ], gap=2).style({"padding": "20px 0"})
    return (history_tab,)


@app.cell
def _(history_tab, mo, results_tab):
    _navbar = mo.Html("""
    <div class="navbar">
      <div><span class="navbar-title">FRICTION EVALUATION</span><span class="navbar-version">v2.0</span></div>
      <span class="navbar-user">Marimo</span>
    </div>
    """)

    mo.vstack([
        _navbar,
        mo.ui.tabs({
            "📊  Analysis":  results_tab,
            "🗂  History":   history_tab,
        }),
    ], gap=0).style({"max-width": "1280px", "margin": "0 auto"})
    return


if __name__ == "__main__":
    app.run()
