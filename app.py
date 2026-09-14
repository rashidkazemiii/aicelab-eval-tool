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
    import settings_store

    return charts, data_loader, mo, pipeline, results_table, settings_store, table_helpers


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
      .navbar-right { display: flex; align-items: center; gap: 14px; }
      .navbar-help {
        color: #4cceac; font-size: 0.78rem; font-weight: 600; text-decoration: none;
        border: 1px solid #4cceac; border-radius: 5px; padding: 4px 10px;
      }
      .navbar-help:hover { background: #4cceac; color: #1f2a40; }
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
      /* marimo colors a form's submit button yellow/orange when the fields
         differ from what was last submitted, and gray once they match -
         a "pending changes" cue that reads as "broken/disabled" here. Force
         one plain, always-the-same button color instead - targeting the
         real type="submit" attribute (not just data-testid) since that's
         the one thing guaranteed to still be on the button in a production
         build. */
      button[type="submit"],
      button[type="submit"][data-testid="marimo-plugin-form-submit-button"] {
        background-color: #1f2a40 !important;
        background: #1f2a40 !important;
        border-color: #1f2a40 !important;
        color: #fff !important;
        box-shadow: none !important;
      }
      button[type="submit"]:hover {
        background-color: #16202f !important;
        background: #16202f !important;
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
    # Snapshot of the Filter fields taken when Filter was clicked, plus the
    # file it was clicked for. The snapshot is what actually gets applied -
    # editing the fields afterwards doesn't re-filter anything until Filter
    # is clicked again. The file id is what stops a Filter clicked for an
    # earlier file from silently carrying over to the next one.
    get_filter_params, set_filter_params = mo.state(None)
    return get_filter_params, set_filter_params


@app.cell
def _(mo):
    get_filter_file_id, set_filter_file_id = mo.state(None)
    return get_filter_file_id, set_filter_file_id


@app.cell
def _(mo):
    get_eval_params, set_eval_params = mo.state(None)
    return get_eval_params, set_eval_params


@app.cell
def _(mo):
    get_eval_file_id, set_eval_file_id = mo.state(None)
    return get_eval_file_id, set_eval_file_id


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
    offset_btn = mo.ui.run_button(label="Offset")
    return (offset_btn,)


@app.cell
def _(offset_btn, set_offset):
    # Toggles in its own cell rather than through an on_change on the button,
    # so the cell that builds offset_btn never has to reference get_offset
    # (which would rebuild the button on every click). The updater-function
    # form of the setter flips the value without reading it here either.
    if offset_btn.value:
        set_offset(lambda was_on: not was_on)
    return


@app.cell
def _(mo):
    save_btn = mo.ui.run_button(label="💾 Save")
    return (save_btn,)


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
def _(has_step_checkbox, mo, settings_store):
    # Deliberately does not depend on file_upload: marimo reconstructs every
    # mo.ui element in this cell (resetting it to its literal value= here)
    # whenever the cell re-runs, and it used to depend on file_upload just to
    # default Stop Main Data to the new file's line count - so every fresh
    # upload wiped out every field here, not just that one. Not needed:
    # parse_main_and_step_data already treats stop_main_row <= start_main_row
    # (0 included) as "read to the end of the file" (data_loader.py:39-42),
    # so a plain static default gets the same result without the coupling.
    #
    # Also deliberately does NOT depend on get_last_raw_params (the reactive
    # state set right after each Calculate submission): that would make this
    # cell - and therefore raw_data_form itself - get rebuilt as a brand-new
    # object right after every single Calculate click, which is exactly the
    # kind of churn this cell is designed to avoid elsewhere. Reading the
    # settings file directly is a plain function call, not a tracked
    # reactive value, so it seeds the fields once (on startup, or whenever
    # this cell happens to re-run for another reason, like the checkbox
    # below) without creating that dependency.
    _saved = settings_store.load_raw_data_settings() or {}
    _step_fields_disabled = not has_step_checkbox.value
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
        + _row.format(label="Drehzahl col #", field="step_col_speed")
        + _grid_close
        + '<hr class="divider">'
        '<p class="section-label" style="margin:0">MAIN DATA</p>'
        + _grid_open
        + _row.format(label="Start Main Data", field="start_main_row")
        + _row.format(label="Stop Main Data (0 = end of file)", field="stop_main_row")
        + _row.format(label="Time col #", field="col_time")
        + _row.format(label="Friction Left col #", field="col_left")
        + _row.format(label="Friction Right col #", field="col_right")
        + _row.format(label="Normal Load col #", field="col_load")
        + _grid_close
        + '</div>'
    )
    raw_data_form = _raw_data_tpl.batch(
        nlc=mo.ui.text(value=_saved.get("nlc", "")),
        start_step_row=mo.ui.text(value=_saved.get("start_step_row", "0"), disabled=_step_fields_disabled),
        end_step_row=mo.ui.text(value=_saved.get("end_step_row", "0"), disabled=_step_fields_disabled),
        step_col_time=mo.ui.text(value=_saved.get("step_col_time", "1"), disabled=_step_fields_disabled),
        step_col_speed=mo.ui.text(value=_saved.get("step_col_speed", "0"), disabled=_step_fields_disabled),
        start_main_row=mo.ui.text(value=_saved.get("start_main_row", "41")),
        stop_main_row=mo.ui.text(value=_saved.get("stop_main_row", "0")),
        col_time=mo.ui.text(value=_saved.get("col_time", "1")),
        col_left=mo.ui.text(value=_saved.get("col_left", "13")),
        col_right=mo.ui.text(value=_saved.get("col_right", "14")),
        col_load=mo.ui.text(value=_saved.get("col_load", "3")),
    )
    return (raw_data_form,)


@app.cell
def _(mo):
    # A plain button, not a .form() submit button: no yellow/gray "pending
    # changes" color, always looks the same. Its own cell has zero
    # dependencies, so it's never rebuilt - unlike a .form(), a run_button's
    # .value is edge-triggered (True for one render right after the click,
    # then back to False) without needing any "was this a fresh click"
    # identity tracking.
    calculate_btn = mo.ui.run_button(label="Calculate")
    return (calculate_btn,)


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
    filter_fields = _filter_tpl.batch(
        filter_points=mo.ui.text(value="25"),
        method=mo.ui.dropdown(
            options={"VBA-exact (slow)": "vba", "Fast (approximate)": "fast"},
            value="VBA-exact (slow)",
        ),
    )
    return (filter_fields,)


@app.cell
def _(mo):
    filter_btn = mo.ui.run_button(label="Filter")
    return (filter_btn,)


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
    eval_fields = _eval_tpl.batch(
        static_range=mo.ui.text(value="10.0"),
        dyn_min=mo.ui.text(value="20.0"),
        dyn_max=mo.ui.text(value="80.0"),
    )
    return (eval_fields,)


@app.cell
def _(mo):
    eval_btn = mo.ui.run_button(label="Evaluate")
    return (eval_btn,)


# ── Data pipeline ──────────────────────────────────────────────────────────
@app.cell
def _(
    calculate_btn,
    data_loader,
    file_upload,
    get_parsed_data,
    has_step_checkbox,
    mo,
    raw_data_form,
    set_parsed_data,
    set_results_status_msg,
    settings_store,
):
    # raw_data_form is a plain, live batch now (not a .form()) - its .value
    # updates on every keystroke, but that alone doesn't do anything here:
    # the actual parse only runs when calculate_btn.value is True, which is
    # only the case for the one render right after Calculate is clicked
    # (a run_button's value is edge-triggered, back to False immediately
    # after). Typing still causes this cell to re-run (raw_data_form is a
    # dependency), but each such re-run just evaluates this condition as
    # False and falls through to re-reading get_parsed_data() unchanged.
    _p = raw_data_form.value
    if calculate_btn.value:
        # Every Calculate press wipes out whatever was previously computed
        # first, then parses fresh from the raw file - never patches or
        # reuses the old result.
        set_parsed_data(None)
        settings_store.save_raw_data_settings(_p)
        if data_loader.is_ready_to_parse(bool(file_upload.value), _p):
            try:
                _raw = file_upload.value[0].contents.decode("latin-1")
                _p = dict(_p)
                _p["has_step"] = has_step_checkbox.value
                _df_raw, _step_df = data_loader.parse_main_and_step_data(_raw, _p)
                # Tagged with the file it was parsed from (name, size), so a
                # later upload can't leave stale results looking like they
                # belong to the new file - see the df_display cell below,
                # which is the one place that actually has to make that call.
                _file_id = (file_upload.value[0].name, len(file_upload.value[0].contents))
                set_parsed_data((_df_raw, _step_df, _p, _file_id))
                set_results_status_msg(mo.callout(
                    mo.md(f"**{file_upload.value[0].name}** — {len(_df_raw):,} rows, {len(_df_raw.columns)} columns: `{list(_df_raw.columns)}`"),
                    kind="success",
                ))
            except Exception as _e:
                set_parsed_data((None, None, None, None))
                set_results_status_msg(mo.callout(mo.md(f"**Error:** {_e}"), kind="danger"))

    _parsed = get_parsed_data()
    if _parsed is None:
        df_raw = None
        step_df = None
        committed_params = None
        parsed_file_id = None
    else:
        df_raw, step_df, committed_params, parsed_file_id = _parsed
    return committed_params, df_raw, parsed_file_id, step_df


@app.cell
def _(mo):
    get_seen_upload_id, set_seen_upload_id = mo.state(None)
    return get_seen_upload_id, set_seen_upload_id


@app.cell
def _(file_upload, get_seen_upload_id, set_parsed_data, set_seen_upload_id):
    # Wipes any previously-calculated result the instant a different file
    # lands in the upload box - before Calculate is even pressed - so the
    # old file's data/chart never lingers behind a new upload. Guarded by
    # get_seen_upload_id so this only fires once per actual file change, not
    # on every rerun this cell happens to be part of.
    _current_file_id = (
        (file_upload.value[0].name, len(file_upload.value[0].contents))
        if file_upload.value else None
    )
    if _current_file_id != get_seen_upload_id():
        set_seen_upload_id(_current_file_id)
        set_parsed_data(None)
    return


@app.cell
def _(committed_params, df_raw, file_upload, get_offset, mo, parsed_file_id, pipeline, set_results_status_msg, step_df):
    # df_raw sticks around (by design - see the pipeline cell above) so
    # editing a field doesn't blank the result until Calculate is clicked
    # again. But that means it can also still be holding a previous file's
    # data after a new upload with no Calculate click for it yet - checking
    # its tagged file id against what's actually in file_upload right now is
    # what actually clears the chart for the new file, right here where
    # df_display (the chart's real input) gets built, rather than relying on
    # a separate step to clear it proactively somewhere upstream.
    _current_file_id = (
        (file_upload.value[0].name, len(file_upload.value[0].contents))
        if file_upload.value else None
    )
    df_display = None
    if df_raw is not None and parsed_file_id == _current_file_id:
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
def _(
    df_display,
    filter_btn,
    filter_fields,
    get_filter_file_id,
    get_filter_params,
    mo,
    parsed_file_id,
    pipeline,
    set_filter_file_id,
    set_filter_params,
    set_results_status_msg,
):
    if filter_btn.value:
        set_filter_params(filter_fields.value)
        set_filter_file_id(parsed_file_id)
    # None (not yet run for the file that's active right now) unless Filter
    # was actually clicked while this same file was the one loaded.
    active_filter_params = get_filter_params() if get_filter_file_id() == parsed_file_id else None
    if df_display is not None:
        try:
            df_proc = pipeline.compute_filtered_df(df_display, active_filter_params)
        except Exception as _e:
            df_proc = df_display.copy()
            set_results_status_msg(mo.callout(mo.md(f"**Filter error:** {_e}"), kind="danger"))
    else:
        df_proc = None
    return active_filter_params, df_proc


@app.cell
def _(
    df_display,
    df_proc,
    eval_btn,
    eval_fields,
    get_eval_file_id,
    get_eval_params,
    mo,
    parsed_file_id,
    pipeline,
    set_eval_file_id,
    set_eval_params,
    set_results_status_msg,
):
    if eval_btn.value:
        set_eval_params(eval_fields.value)
        set_eval_file_id(parsed_file_id)
    active_eval_params = get_eval_params() if get_eval_file_id() == parsed_file_id else None
    cof_eval = None
    try:
        cof_eval = pipeline.compute_evaluation(df_display, df_proc, active_eval_params)
    except Exception as _e:
        set_results_status_msg(mo.callout(mo.md(f"**Evaluate error:** {_e}"), kind="danger"))
    return active_eval_params, cof_eval


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
    active_eval_params,
    active_filter_params,
    cof_eval,
    db_mod,
    df_display,
    df_proc,
    file_upload,
    mo,
    overwrite_btn,
    pipeline,
    save_btn,
    set_results_status_msg,
    stats_result,
):
    # Both save_btn and overwrite_btn are plain run_buttons: True for exactly
    # one render right after their own click, then back to False on their
    # own - so neither needs any "was this actually a new click" tracking.
    _save_clicked = save_btn.value or overwrite_btn.value
    _have_eval_results = cof_eval is not None and stats_result is not None
    _have_file_and_data = bool(file_upload.value) and df_display is not None
    if _save_clicked and _have_eval_results and _have_file_and_data:
        _fname = file_upload.value[0].name
        _fparams = active_filter_params
        _eparams = active_eval_params
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
def _(db_mod, mo, refresh_btn):
    # Reference this so marimo tracks it as a real dependency (reactivity is
    # derived from names actually used in the body, not the signature) - this
    # is what makes Refresh actually re-query the database. Delete is
    # deliberately NOT a dependency here: re-running this cell reconstructs
    # mo.ui.table, which resets its selection - if Delete triggered that
    # rebuild too, it would always find "no row selected" on its own click,
    # since this cell (which produces history_table) runs before the delete
    # cell (which reads history_table.value) in the same pass.
    refresh_btn.value

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
            # Same iframe wrapping as the live CoF Analysis chart, not
            # mo.ui.plotly directly: a saved test's figure is still built
            # from the full per-cycle marker tables, and mo.ui.plotly sends
            # the whole thing through marimo's own reactive output channel,
            # which enforces a size limit the raw HTML iframe below doesn't.
            history_chart = mo.Html(charts.figure_to_zoom_iframe_html(_fig, zoom_key=f"history-{_test_id}"))
    return (history_chart,)


@app.cell
def _(active_filter_params, charts, cof_eval, df_display, df_proc, mo, parsed_file_id, pipeline, step_df):
    if df_display is None:
        cof_chart = mo.Html(
            '<div style="height:360px;display:flex;align-items:center;justify-content:center;'
            'background:#fafafa;border-radius:6px;color:#bbb;font-size:13px">'
            "Upload a file to see the chart</div>"
        )
    else:
        _filter_active = pipeline.is_filter_active(active_filter_params, df_proc)
        _fig = charts.build_cof_figure(df_display, df_proc, cof_eval, step_df, _filter_active)
        # df_display only ever gets built from data tagged with the file
        # that's actually in the upload box right now (see the df_display
        # cell above) - so this name is never stale, unlike just reading
        # file_upload directly here would risk if the two ever raced.
        _fname = parsed_file_id[0] if parsed_file_id else "—"
        cof_chart = mo.vstack([
            mo.Html(f'<p style="font-size:0.72rem;color:#888;margin:0 0 4px 0">'
                     f'Showing: <strong>{_fname}</strong></p>'),
            mo.Html(charts.figure_to_zoom_iframe_html(_fig, zoom_key="live")),
        ], gap=0)
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
    active_filter_params,
    cof_eval,
    data_loader,
    df_display,
    df_proc,
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
            _filter_active = pipeline.is_filter_active(active_filter_params, df_proc)
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
# Split into independent cells (rather than one monolithic layout cell) so
# that a widget somewhere getting rebuilt with a new identity - which
# happens legitimately whenever get_results_status_msg()'s content changes,
# i.e. after nearly every action in the app - only forces a re-render of
# the one small card that actually reads it, instead of resending the
# entire tab (chart included) and risking the frontend losing its
# connection to every other button in the process.
@app.cell
def _(file_upload, get_results_status_msg, mo, open_excel_btn, PANEL_STYLE, parsed_file_id):
    if file_upload.value:
        _rvm_test = file_upload.value[0].name.replace(".txt", "")
    else:
        _rvm_test = "—"

    # Raw Data's fields deliberately keep their values across an upload (see
    # raw_data_form's own cell) instead of resetting to defaults - but that
    # also means the Calculate button's color (marimo grays it out once the
    # fields match what was last submitted) stops being a reliable "you still
    # need to press this" cue: a newly uploaded file whose fields happen to
    # already match won't turn the button yellow again. This banner is the
    # explicit substitute - it compares the file actually in the upload box
    # against the one the current results were parsed from.
    _current_file_id = (
        (file_upload.value[0].name, len(file_upload.value[0].contents))
        if file_upload.value else None
    )
    if file_upload.value and _current_file_id != parsed_file_id:
        _status = mo.callout(mo.md("**New file uploaded** — click **Calculate** to parse it."), kind="warn")
    else:
        _status = get_results_status_msg()

    upload_card = mo.vstack([
        mo.hstack([file_upload, open_excel_btn], justify="start", align="center"),
        _status,
        mo.Html('<hr class="divider">'),
        mo.Html(f'<div style="display:flex;flex-direction:column;gap:2px">'
                f'<span style="font-size:0.6rem;color:#999;font-weight:700;letter-spacing:1px">RVM TEST</span>'
                f'<span style="font-size:0.9rem;font-weight:600;color:#1f2a40">{_rvm_test}</span></div>'),
    ], gap=1).style(PANEL_STYLE)
    return (upload_card,)


@app.cell
def _(calculate_btn, has_step_checkbox, mo, PANEL_STYLE, raw_data_form):
    raw_data_card = mo.vstack([
        mo.Html('<p class="panel-title">Raw Data</p>'),
        has_step_checkbox,
        raw_data_form,
        calculate_btn,
    ], gap=2).style(PANEL_STYLE)
    return (raw_data_card,)


@app.cell
def _(
    ACTION_CARD_STYLE,
    eval_btn,
    eval_fields,
    filter_btn,
    filter_fields,
    get_offset,
    mo,
    offset_btn,
    save_btn,
):
    _offset_badge = (
        mo.Html('<span style="font-size:0.7rem;color:#4cceac;font-weight:700">ON</span>')
        if get_offset() else mo.Html("")
    )
    actions_row = mo.hstack([
        mo.vstack([mo.Html('<p class="section-label" style="margin:0">ACTIONS</p>'), offset_btn, _offset_badge], gap=1, justify="space-between").style(ACTION_CARD_STYLE),
        mo.vstack([mo.Html('<p class="section-label" style="margin:0">FILTER</p>'), filter_fields, filter_btn], gap=1, justify="space-between").style(ACTION_CARD_STYLE),
        mo.vstack([mo.Html('<p class="section-label" style="margin:0">EVALUATE</p>'), eval_fields, eval_btn], gap=1, justify="space-between").style(ACTION_CARD_STYLE),
        mo.vstack([mo.Html('<p class="section-label" style="margin:0">SAVE</p>'), save_btn], gap=1, justify="space-between").style(ACTION_CARD_STYLE),
    ], gap=2, align="stretch", widths="equal")
    return (actions_row,)


@app.cell
def _(cof_chart, mo, PANEL_STYLE, results_panel):
    viz_card = mo.vstack([
        mo.Html('<p class="panel-title">Analysis Visualization</p>'),
        cof_chart,
        mo.Html('<hr class="divider">'),
        results_panel,
    ], gap=1).style(PANEL_STYLE)
    return (viz_card,)


@app.cell
def _(actions_row, mo, raw_data_card, upload_card, viz_card):
    results_tab = mo.vstack([
        upload_card,
        raw_data_card,
        actions_row,
        viz_card,
    ], gap=2).style({"padding": "20px 0"})
    return (results_tab,)


@app.cell
def _(PANEL_STYLE, delete_btn, get_history_status_msg, history_table, mo, refresh_btn):
    tests_card = mo.vstack([
        mo.hstack([refresh_btn, delete_btn], gap=2, justify="start"),
        get_history_status_msg(),
        mo.Html('<hr class="divider">'),
        mo.Html('<p class="panel-title">Saved Tests</p>'),
        history_table,
    ], gap=2).style(PANEL_STYLE)
    return (tests_card,)


@app.cell
def _(PANEL_STYLE, cycles_panel, history_chart, mo):
    chart_card = mo.vstack([
        mo.Html('<p class="panel-title">Chart</p>'),
        history_chart,
        mo.Html('<hr class="divider">'),
        cycles_panel,
    ], gap=1).style(PANEL_STYLE)
    return (chart_card,)


@app.cell
def _(chart_card, mo, tests_card):
    history_tab = mo.vstack([
        tests_card,
        chart_card,
    ], gap=2).style({"padding": "20px 0"})
    return (history_tab,)


@app.cell
def _(mo):
    import pathlib as _pathlib
    import webbrowser as _webbrowser

    # A plain <a href="file://..."> link doesn't work here: the app is served
    # over http://localhost, and browsers silently block navigation from an
    # http(s) page to a file:// URL (it just does nothing, no error, no
    # console message). Opening the browser from the Python side instead
    # (via a button's on_click) sidesteps that restriction entirely, since
    # it isn't a same-page navigation at all.
    _help_url = (_pathlib.Path(__file__).parent / "docs_cof_math.html").resolve().as_uri()

    def _open_help(value):
        _webbrowser.open(_help_url)
        return value

    help_button = mo.ui.button(label="❓ Help", on_click=_open_help)
    return (help_button,)


@app.cell
def _(mo):
    # A separate flag from get_offset/get_last_raw_params etc.: which of the
    # two main sections (Analysis vs History) is currently shown.
    get_active_tab, set_active_tab = mo.state("results")
    return get_active_tab, set_active_tab


@app.cell
def _(mo, set_active_tab):
    # Deliberately does not depend on get_active_tab: unlike mo.ui.tabs
    # (a single stateful, interactive component that owns its own "which
    # tab" state internally), these are two plain buttons whose own identity
    # never needs to change - switching tabs only has to update which
    # content is shown below them, not rebuild the switcher itself.
    def _show_results(_v):
        set_active_tab("results")
        return _v

    def _show_history(_v):
        set_active_tab("history")
        return _v

    tab_results_btn = mo.ui.button(label="📊  Analysis", on_click=_show_results)
    tab_history_btn = mo.ui.button(label="🗂  History", on_click=_show_history)
    return tab_history_btn, tab_results_btn


@app.cell
def _(get_active_tab, help_button, history_tab, mo, results_tab, tab_history_btn, tab_results_btn):
    # mo.ui.tabs previously wrapped results_tab/history_tab directly. That
    # meant the outermost, page-wide wrapper was itself a stateful,
    # interactive widget that got rebuilt as a brand-new object every time
    # results_tab changed identity - which happens repeatedly (confirmed via
    # debug logging: 5 rebuilds from a single Calculate click alone), since
    # results_tab's own combiner cell depends on several cards that each
    # update at a different point in the reactive cascade. Rebuilding an
    # interactive tabs component that many times in a row is the most
    # plausible explanation for raw_data_form's Calculate button losing its
    # connection afterward. Plain conditional rendering below has no
    # equivalent "own state to reinitialize" - only the two buttons above
    # are truly interactive, and they never get rebuilt.
    _navbar = mo.Html(f"""
    <div class="navbar">
      <div><span class="navbar-title">FRICTION EVALUATION</span><span class="navbar-version">v2.0</span></div>
      <div class="navbar-right">
        {help_button}
        <span class="navbar-user">Marimo</span>
      </div>
    </div>
    """)

    _active = get_active_tab()
    _results_underline = 'border-bottom:2px solid #4cceac' if _active == "results" else 'border-bottom:2px solid transparent'
    _history_underline = 'border-bottom:2px solid #4cceac' if _active == "history" else 'border-bottom:2px solid transparent'

    _switcher = mo.hstack([
        mo.Html(f'<div style="{_results_underline};padding-bottom:2px">{tab_results_btn}</div>'),
        mo.Html(f'<div style="{_history_underline};padding-bottom:2px">{tab_history_btn}</div>'),
    ], gap=2, justify="start")

    _content = results_tab if _active == "results" else history_tab

    mo.vstack([
        _navbar,
        _switcher,
        _content,
    ], gap=0).style({"max-width": "1280px", "margin": "0 auto"})
    return


if __name__ == "__main__":
    app.run()
