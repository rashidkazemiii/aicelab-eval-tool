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
    import speed_pulse
    import batch
    import ai_model
    import info_fields

    return ai_model, batch, charts, data_loader, info_fields, mo, pipeline, results_table, settings_store, speed_pulse, table_helpers


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
    # Same card look, but slim: one row of controls (the Offset / Filter /
    # Evaluate toolbar) instead of a panel with a title.
    TOOLBAR_STYLE = {
        "background": "#fff",
        "border-radius": "8px",
        "padding": "10px 16px",
        "box-shadow": "0 1px 4px rgba(0,0,0,0.08)",
    }
    # A box inside a panel: a thin line instead of a shadow.
    SUB_PANEL_STYLE = {
        "border": "1px solid #eee",
        "border-radius": "8px",
        "padding": "16px",
        "height": "100%",
        "box-sizing": "border-box",
    }
    return PANEL_STYLE, SUB_PANEL_STYLE, TOOLBAR_STYLE


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
    # The file "Find zeros" was last clicked for, so a click for an earlier
    # file never carries over to the next one.
    get_zeros_file_id, set_zeros_file_id = mo.state(None)
    return get_zeros_file_id, set_zeros_file_id


@app.cell
def _(mo):
    # Which evaluation the page shows:
    #   "zeros" - none, only the zero crossings (after Find zeros);
    #   "pulse" - the chart's Evaluate with pulse result;
    #   "saved" - the evaluation stored with a test loaded from the Database tab.
    # Whichever action happened last wins.
    get_eval_mode, set_eval_mode = mo.state("zeros")
    return get_eval_mode, set_eval_mode


@app.cell
def _(mo):
    # Snapshot taken when "Evaluate with pulse" is clicked: the pulse edges
    # (offsets applied), the Evaluate fields, and the file it was clicked
    # for. The pulse evaluation is computed from this snapshot only, so
    # moving an offset afterwards moves the drawn pulse but not the results
    # until the button is clicked again.
    get_pulse_eval_request, set_pulse_eval_request = mo.state(None)
    return get_pulse_eval_request, set_pulse_eval_request


@app.cell
def _(mo):
    # The last click of "Evaluate with pulse": the offsets typed in, the
    # Evaluate fields, the file and the click id ("nonce", so the same click
    # is never handled twice). "done" is False until the evaluation has been
    # started - a click may first have to wait for Offset, Filter and Find
    # zeros to run.
    get_pulse_click, set_pulse_click = mo.state(None)
    return get_pulse_click, set_pulse_click


@app.cell
def _(mo):
    # A saved test brought back from the Database tab ("Load into Analysis"):
    # None, or the dict database.load_test_for_analysis returns. While set,
    # the Analysis pipeline shows that test instead of an uploaded file -
    # the signal, filter, evaluation and steps come from the database, and
    # Filter / Find zeros / Evaluate with pulse / Save then work on it as on
    # an uploaded file. Cleared by the next Calculate click.
    get_loaded_test, set_loaded_test = mo.state(None)
    return get_loaded_test, set_loaded_test


@app.cell
def _(mo):
    # What the Filter / Evaluate boxes should show. Only "Load into
    # Analysis" writes it, so the toolbar is rebuilt for that one action and
    # for nothing else - typing, Calculate, Filter, Evaluate and Offset all
    # leave the boxes (and the page) alone. None means the defaults.
    get_box_values, set_box_values = mo.state(None)
    return get_box_values, set_box_values


@app.cell
def _(mo):
    # One shared status message per tab, each shown in a single place on
    # that tab's page. Whichever action on that tab last had something to
    # say calls its set_..._status_msg() to replace it - so each tab has
    # exactly one message box, always showing that tab's own latest action,
    # instead of every action having its own separate, independently-timed
    # message box scattered around the page. Kept as two separate states
    # (not one shared one) so an action on the Analysis tab never overwrites
    # what's showing on the Database tab, or vice versa.
    get_results_status_msg, set_results_status_msg = mo.state(
        mo.callout(mo.md("Set the row numbers, then click **Calculate**."), kind="info")
    )
    return get_results_status_msg, set_results_status_msg


@app.cell
def _(mo):
    # A counter that goes up by one every time the Analysis tab saves a
    # test. The Database tab's table reads it, so it re-reads the database
    # after every save and the new test shows up right away.
    get_tests_version, set_tests_version = mo.state(0)
    return get_tests_version, set_tests_version


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
    save_anyway_btn = mo.ui.run_button(label="Save anyway")
    return (save_anyway_btn,)


@app.cell
def _(mo):
    overwrite_btn = mo.ui.run_button(label="Overwrite & Save")
    return (overwrite_btn,)


@app.cell
def _(mo):
    # The answer to the last Save click (empty fields, already saved, done),
    # shown right under the save form.
    get_save_msg, set_save_msg = mo.state(None)
    return get_save_msg, set_save_msg


@app.cell
def _(mo):
    # Goes up by one whenever a column is added or deleted on the Database
    # tab: every form and table that lists the columns reads it.
    get_columns_version, set_columns_version = mo.state(0)
    return get_columns_version, set_columns_version


@app.cell
def _(mo):
    # Goes up by one whenever information is edited or a test is deleted on
    # the Database tab.
    get_database_version, set_database_version = mo.state(0)
    return get_database_version, set_database_version


@app.cell
def _(info_fields, mo):
    def form_rows_html(rows):
        """A form with one box per row, all boxes the same width and exactly
        under each other. `rows` is a list of (label, box, unit)."""
        _html = ('<div style="display:grid;grid-template-columns:max-content 280px max-content;'
                 'align-items:center;gap:10px 12px">')
        for _label, _box, _unit in rows:
            _html += (f'<span style="font-size:0.82rem;color:#444;white-space:nowrap">{_label}</span>'
                      f'<div>{_box}</div>'
                      f'<span style="font-size:0.82rem;color:#888;white-space:nowrap">{_unit}</span>')
        _html += '</div>'
        return _html

    def build_info_form(columns, values):
        """One text box per information column, one per row, filled with
        `values` ({column id: value}). `.value` gives {column key: typed
        text}."""
        _boxes = {}
        _rows = []
        for _column in columns:
            _label = info_fields.html_label(_column["name"])
            _unit = info_fields.html_label(_column["unit"])
            _rows.append((_label, "{" + _column["key"] + "}", _unit))
            _boxes[_column["key"]] = mo.ui.text(
                value=info_fields.value_as_text(values.get(_column["id"])),
                full_width=True,
            )
        return mo.Html(form_rows_html(_rows)).batch(**_boxes)
    return build_info_form, form_rows_html


@app.cell
def _(mo):
    # Kept outside the form (live, not submit-only) so unchecking it can
    # grey out the step fields below right away, without needing "Calculate".
    has_step_checkbox = mo.ui.checkbox(label="Has step data", value=True)
    return (has_step_checkbox,)




@app.cell
def _(data_loader, file_upload, mo):
    # A download, not "open Excel here": when the app runs as a server, the
    # file has to land on the user's own computer, where they open it in
    # Excel. The .csv is only built when the button is clicked.
    if file_upload.value:
        _upload = file_upload.value[0]
        _base_name = _upload.name.replace(".txt", "")

        def _build_raw_csv():
            return data_loader.raw_text_to_csv_bytes(_upload.contents.decode("latin-1"))

        open_excel_btn = mo.download(
            data=_build_raw_csv,
            filename=f"{_base_name}.csv",
            mimetype="text/csv",
            label="&#128194; Open in Excel",
        )
    else:
        open_excel_btn = mo.download(
            data=b"", filename="raw_data.csv", disabled=True,
            label="&#128194; Open in Excel",
        )
    return (open_excel_btn,)


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
    set_loaded_test,
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
        # reuses the old result. A test loaded from the Database tab is dropped too.
        set_parsed_data(None)
        set_loaded_test(None)
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
                    mo.md(f"**{file_upload.value[0].name}** &mdash; {len(_df_raw):,} rows, {len(_df_raw.columns)} columns: `{list(_df_raw.columns)}`"),
                    kind="success",
                ))
            except Exception as _e:
                set_parsed_data((None, None, None, None))
                set_results_status_msg(mo.callout(mo.md(f"**Error:** {_e}"), kind="danger"))

    return


@app.cell
def _(calculate_btn, get_loaded_test, get_parsed_data):
    # Reads only the snapshots, never the Raw Data boxes - so editing one of
    # those re-runs the parse cell above (which does nothing without a
    # Calculate click) and stops there, instead of rebuilding the pipeline.
    _parsed = get_parsed_data()
    # Right after a Calculate click the loaded test is gone no matter what
    # the state still reads in this same run.
    if calculate_btn.value:
        _loaded = None
    else:
        _loaded = get_loaded_test()
    if _loaded is not None:
        # A saved test from the Database tab stands in for a parsed file. Its id is
        # (file name, "test-<id>") so Filter / Evaluate clicks are tracked
        # per loaded test just like per uploaded file.
        df_raw = None
        step_df = _loaded["step_df"]
        committed_params = None
        parsed_file_id = (_loaded["file_name"], "test-%d" % _loaded["test_id"])
    elif _parsed is None:
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
def _(file_upload, get_seen_upload_id, set_loaded_test, set_parsed_data, set_seen_upload_id):
    # Wipes any previously-calculated result the instant a different file
    # lands in the upload box - before Calculate is even pressed - so the
    # old file's data/chart never lingers behind a new upload. A test that
    # was loaded from the Database tab is dropped here as well, for the same reason:
    # once a different file is in the box, its chart and evaluated cycles
    # are not what the page should be showing. Guarded by
    # get_seen_upload_id so this only fires once per actual file change, not
    # on every rerun this cell happens to be part of.
    _current_file_id = (
        (file_upload.value[0].name, len(file_upload.value[0].contents))
        if file_upload.value else None
    )
    if _current_file_id != get_seen_upload_id():
        set_seen_upload_id(_current_file_id)
        set_parsed_data(None)
        set_loaded_test(None)
    return


@app.cell
def _(committed_params, df_raw, file_upload, get_loaded_test, get_offset, mo, parsed_file_id, pipeline, set_results_status_msg, step_df):
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
    _loaded = get_loaded_test()
    if _loaded is not None:
        df_display = _loaded["df_display"]
    elif df_raw is not None and parsed_file_id == _current_file_id:
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
def _(filter_btn, filter_fields, parsed_file_id, set_filter_file_id, set_filter_params):
    # Reading a text box's value in a cell makes that cell re-run whenever
    # the value is committed. So the reading happens here, in a cell that
    # produces nothing and does nothing unless Filter was actually clicked -
    # the filtering itself is the next cell, which only sees the snapshot.
    # Keeping the two together is what used to re-filter, re-evaluate and
    # redraw the whole page on every edit.
    if filter_btn.value:
        set_filter_params(filter_fields.value)
        set_filter_file_id(parsed_file_id)
    return


@app.cell
def _(
    df_display,
    get_filter_file_id,
    get_filter_params,
    get_loaded_test,
    mo,
    parsed_file_id,
    pipeline,
    set_results_status_msg,
):
    # None (not yet run for the file that's active right now) unless Filter
    # was actually clicked while this same file was the one loaded.
    _filter_clicked_here = get_filter_file_id() == parsed_file_id
    _loaded = get_loaded_test()
    if _loaded is not None and not _filter_clicked_here:
        # Test from the Database tab, Filter not clicked since: show it as saved.
        active_filter_params = _loaded["filter_params"]
        df_proc = _loaded["df_proc"]
    else:
        active_filter_params = get_filter_params() if _filter_clicked_here else None
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
def _(find_zeros_btn, parsed_file_id, set_eval_mode, set_zeros_file_id):
    # "Find zeros" only finds the zero crossings; the cycles are evaluated
    # with the chart's "Evaluate with pulse" button. A new Find zeros click
    # hides the previous pulse evaluation, because that one was made with
    # the old crossings.
    if find_zeros_btn.value:
        set_zeros_file_id(parsed_file_id)
        set_eval_mode("zeros")
    return


@app.cell
def _(
    df_proc,
    get_loaded_test,
    get_zeros_file_id,
    mo,
    parsed_file_id,
    pipeline,
    set_results_status_msg,
):
    _zeros_clicked_here = get_zeros_file_id() == parsed_file_id
    _loaded = get_loaded_test()
    zero_crossings = None
    if _loaded is not None and not _zeros_clicked_here:
        # Test from the Database tab, Find zeros not clicked since: use the
        # crossings stored with its evaluation.
        zero_crossings = _loaded["cof_eval"]["minima"]
    elif _zeros_clicked_here:
        try:
            zero_crossings = pipeline.compute_zero_crossings(df_proc)
        except Exception as _e:
            set_results_status_msg(mo.callout(mo.md(f"**Find zeros error:** {_e}"), kind="danger"))
    return (zero_crossings,)


@app.cell
def _(charts, mo):
    # Hidden text field the chart's "Evaluate with pulse" button writes into
    # (see setupPulseOffset() in charts.py). It is found by its placeholder,
    # so that must stay PULSE_EVAL_PLACEHOLDER. Nothing that renders the
    # page depends on it - only the handler cell below.
    pulse_eval_field = mo.ui.text(value="", placeholder=charts.PULSE_EVAL_PLACEHOLDER)
    return (pulse_eval_field,)


@app.cell
def _(file_upload, get_loaded_test):
    # The file the Analysis tab is working on: the test loaded from the Database tab
    # if there is one, else the uploaded file. None when neither.
    _loaded = get_loaded_test()
    if _loaded is not None:
        analysis_file_name = _loaded["file_name"]
    elif file_upload.value:
        analysis_file_name = file_upload.value[0].name
    else:
        analysis_file_name = None
    return (analysis_file_name,)


@app.cell
def _(
    eval_fields,
    filter_fields,
    get_filter_file_id,
    get_loaded_test,
    get_offset,
    get_pulse_click,
    get_zeros_file_id,
    mo,
    parsed_file_id,
    pulse_eval_field,
    set_filter_file_id,
    set_filter_params,
    set_offset,
    set_pulse_click,
    set_results_status_msg,
    set_zeros_file_id,
):
    # Handles a click of the chart's "Evaluate with pulse" button. The field
    # holds JSON {"offsets_ms": {step index: ms}, "nonce": click id}. Only a
    # click not seen before is acted on - this cell also re-runs when a box
    # changes, and must not act then.
    #
    # The evaluation needs the Offset, Filter and Find zeros steps: without
    # them the signal is not centred on zero and the pulse is not anchored
    # on the crossings. So any step not done yet for this file is started
    # here, the way its own button does, and a step already done is not
    # repeated. The next cell evaluates once these have finished. A test
    # loaded from the Database tab brings its own results of these steps along.
    import json as _json
    _request = None
    if pulse_eval_field.value:
        try:
            _request = _json.loads(pulse_eval_field.value)
        except ValueError:
            _request = None
    _previous = get_pulse_click()
    _is_new_click = (
        _request is not None
        and (_previous is None or _previous["nonce"] != _request.get("nonce"))
    )
    if _is_new_click:
        _filter_needed = get_loaded_test() is None and get_filter_file_id() != parsed_file_id
        _filter_ok = True
        if _filter_needed:
            try:
                int(filter_fields.value["filter_points"])
            except ValueError:
                _filter_ok = False
        if _filter_ok:
            if get_loaded_test() is None:
                if not get_offset():
                    set_offset(True)
                if _filter_needed:
                    set_filter_params(filter_fields.value)
                    set_filter_file_id(parsed_file_id)
                if get_zeros_file_id() != parsed_file_id:
                    set_zeros_file_id(parsed_file_id)
            set_pulse_click({
                "offsets_ms": _request.get("offsets_ms", {}),
                "params": eval_fields.value,
                "file_id": parsed_file_id,
                "nonce": _request.get("nonce"),
                "done": False,
            })
        else:
            set_pulse_click({"nonce": _request.get("nonce"), "file_id": parsed_file_id, "done": True})
            set_results_status_msg(mo.callout(mo.md(
                "**Not evaluated:** Filter pts must be a whole number."
            ), kind="warn"))
    return


@app.cell
def _(
    get_filter_file_id,
    get_loaded_test,
    get_offset,
    get_pulse_click,
    get_zeros_file_id,
    mo,
    parsed_file_id,
    pulse,
    set_eval_mode,
    set_pulse_click,
    set_pulse_eval_request,
    set_results_status_msg,
    speed_pulse,
    zero_crossings,
):
    # Starts the evaluation of a click, as soon as Offset, Filter and Find
    # zeros are done for its file. This cell comes after zero_crossings and
    # pulse, so it re-runs when they change and always sees the finished
    # pulse. The snapshot uses the pulse as it is now: anchored on the
    # crossings of the filtered signal.
    _click = get_pulse_click()
    if _click is not None and not _click["done"]:
        _steps_done = get_loaded_test() is not None or (
            get_offset()
            and get_filter_file_id() == parsed_file_id
            and get_zeros_file_id() == parsed_file_id
        )
        _finished_click = dict(_click)
        _finished_click["done"] = True
        if _click["file_id"] != parsed_file_id:
            set_pulse_click(_finished_click)
        elif _steps_done:
            set_pulse_click(_finished_click)
            if pulse is None or zero_crossings is None:
                set_results_status_msg(mo.callout(mo.md(
                    "**Not evaluated:** no speed pulse or zero crossings for this file."
                ), kind="warn"))
            else:
                _offsets_s = {}
                for _key, _ms in _click["offsets_ms"].items():
                    try:
                        _offsets_s[int(_key)] = float(_ms) / 1000.0
                    except (ValueError, TypeError):
                        pass
                set_pulse_eval_request({
                    "edges": speed_pulse.shift_edges(pulse["edges"], _offsets_s),
                    "params": _click["params"],
                    "file_id": _click["file_id"],
                })
                set_eval_mode("pulse")
    return


@app.cell
def _(df_display, get_pulse_eval_request, mo, parsed_file_id, pipeline, set_results_status_msg, step_df):
    _request = get_pulse_eval_request()
    cof_eval_pulse = None
    if _request is not None and _request["file_id"] == parsed_file_id and df_display is not None:
        try:
            cof_eval_pulse = pipeline.compute_pulse_evaluation(
                df_display, _request["edges"], _request["params"]
            )
            if cof_eval_pulse is not None:
                _msg = (
                    f"**Evaluated with pulse:** {len(cof_eval_pulse['cof_res']):,} cycles "
                    "(cycle boundaries = pulse edges, static = first peak up to Dyn min)."
                )
                _skipped_names = []
                for _step_index in cof_eval_pulse["skipped_steps"]:
                    _row = step_df.iloc[_step_index]
                    _skipped_names.append(
                        f"{round(_row['Startzeit [s]'])}-{round(_row['Endzeit [s]'])} s"
                    )
                if len(_skipped_names) > 0:
                    _msg += (
                        " Skipped (too many zero crossings in one stroke): "
                        + ", ".join(_skipped_names) + "."
                    )
                set_results_status_msg(mo.callout(mo.md(_msg), kind="success"))
        except Exception as _e:
            set_results_status_msg(mo.callout(mo.md(f"**Evaluate with pulse error:** {_e}"), kind="danger"))
    return (cof_eval_pulse,)


@app.cell
def _(cof_eval_pulse, get_eval_mode, get_loaded_test, get_pulse_eval_request):
    # The evaluation everything downstream (chart markers, tables, Excel,
    # Save) works with, and the Static/Dyn % values it was made with: the
    # pulse evaluation after Evaluate with pulse, the stored one for a test
    # loaded from the Database tab, otherwise none.
    cof_eval = None
    active_eval_params = None
    _mode = get_eval_mode()
    _loaded = get_loaded_test()
    if _mode == "pulse" and cof_eval_pulse is not None:
        cof_eval = cof_eval_pulse
        active_eval_params = get_pulse_eval_request()["params"]
    elif _mode == "saved" and _loaded is not None:
        cof_eval = _loaded["cof_eval"]
        active_eval_params = _loaded["eval_params"]
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


@app.cell
def _(cof_eval, df_display, pipeline, stats_result, step_df):
    # The same statistics split into CoF+ and CoF- (positive and negative
    # strokes), plus CoF AVG: the two added back together and checked
    # against stats_result. Kept apart from stats_result so a problem here
    # never hides the normal results.
    plus_minus_result = None
    plus_minus_error = None
    if cof_eval is not None and df_display is not None and stats_result is not None:
        try:
            plus_minus_result = pipeline.compute_plus_minus_stats(cof_eval, df_display, step_df, stats_result)
        except Exception as _e:
            plus_minus_error = str(_e)
    return plus_minus_error, plus_minus_result


@app.cell
def _(
    build_info_form,
    data_loader,
    analysis_file_name,
    db_mod,
    file_upload,
    get_columns_version,
    get_loaded_test,
    mo,
):
    # The information asked for when saving. Filled in from the saved test
    # of the same name, if there is one; the stroke of an uploaded file
    # comes from its header.
    #
    # The boxes and the Save button are created AND laid out here, for the
    # same reason as on the Database tab (see db_fill_form): other cells only
    # get save_info_panel, which is plain layout, so typing rebuilds nothing.
    get_columns_version()
    _columns = db_mod.list_info_columns()
    _values = {}
    if analysis_file_name is not None:
        _existing = db_mod.find_existing_test(analysis_file_name)
        if _existing is not None:
            _values = db_mod.get_info_values(_existing.id)
    if get_loaded_test() is None and file_upload.value:
        _stroke = data_loader.read_stroke_mm(file_upload.value[0].contents.decode("latin-1"))
        if _stroke is not None:
            for _column in _columns:
                if _column["field"] == "stroke_mm":
                    _values[_column["id"]] = _stroke

    save_info_form = build_info_form(_columns, _values)
    save_btn = mo.ui.run_button(label="&#128190; Save to database")
    save_info_panel = mo.vstack([
        mo.Html('<p class="section-label" style="margin:12px 0 0 0">SAVE TO DATABASE</p>'),
        mo.md("After evaluating, fill in the information about this test and save it."),
        save_info_form,
        mo.hstack([save_btn], justify="start"),
    ], gap=1)
    return save_btn, save_info_form, save_info_panel


@app.cell
def _(analysis_file_name, set_save_msg):
    # A message about saving one file means nothing for the next one.
    analysis_file_name
    set_save_msg(None)
    return


# ── DB save ────────────────────────────────────────────────────────────────
@app.cell
def _(
    active_eval_params,
    active_filter_params,
    analysis_file_name,
    cof_eval,
    db_mod,
    df_display,
    df_proc,
    info_fields,
    mo,
    overwrite_btn,
    pipeline,
    plus_minus_result,
    save_anyway_btn,
    save_btn,
    save_info_form,
    set_tests_version,
    set_save_msg,
    stats_result,
    step_df,
):
    # The Save, Save anyway and Overwrite buttons are plain run_buttons:
    # True for exactly one render right after their own click, then back to
    # False on their own - so none of them needs any "was this actually a
    # new click" tracking. They are one question after another: Save warns
    # about empty fields, Save anyway goes on from there, and a test of the
    # same name is only replaced after Overwrite.
    _save_clicked = save_btn.value or save_anyway_btn.value or overwrite_btn.value
    if _save_clicked:
        _have_eval_results = cof_eval is not None and stats_result is not None
        _have_file_and_data = analysis_file_name is not None and df_display is not None
        _typed = info_fields.read_typed_values(db_mod.list_info_columns(), save_info_form.value)
        if not _have_eval_results or not _have_file_and_data:
            set_save_msg(mo.callout(mo.md("Evaluate the file first, then save it."), kind="warn"))
        elif len(_typed["not_numbers"]) > 0:
            set_save_msg(mo.callout(mo.md(
                f"**Not saved:** {', '.join(_typed['not_numbers'])} must be a number."
            ), kind="warn"))
        elif save_btn.value and len(_typed["empty"]) > 0:
            set_save_msg(mo.callout(mo.vstack([
                mo.md(
                    f"**Empty:** {', '.join(_typed['empty'])}. Fill these in and click "
                    "**Save** again, or save without them (they can be added later on "
                    "the Database tab)."
                ),
                save_anyway_btn,
            ], gap=1), kind="warn"))
        else:
            _existing = db_mod.find_existing_test(analysis_file_name)
            if _existing is not None and not overwrite_btn.value:
                set_save_msg(mo.callout(mo.vstack([
                    mo.md(
                        f"A test named **{analysis_file_name}** (saved {_existing.uploaded_at}) "
                        "already exists."
                    ),
                    overwrite_btn,
                ], gap=1), kind="warn"))
            else:
                try:
                    if _existing is not None:
                        db_mod.delete_test(_existing.id)
                    _filter_active = pipeline.is_filter_active(active_filter_params, df_proc)
                    _test_id = db_mod.save_full_evaluation(
                        analysis_file_name, active_filter_params, active_eval_params,
                        df_display, df_proc, _filter_active, cof_eval, stats_result,
                        step_df=step_df, plus_minus_result=plus_minus_result,
                    )
                    db_mod.save_info_values(_test_id, _typed["values"])
                    set_save_msg(mo.callout(mo.md(f"Saved as test **#{_test_id}**."), kind="success"))
                    # Makes the Database tab's table re-read the database.
                    set_tests_version(_test_id)
                except Exception as _e:
                    set_save_msg(mo.callout(mo.md(f"**Save failed:** {_e}"), kind="danger"))
    return


# ── Saved tests ────────────────────────────────────────────────────────────
@app.cell
def _():
    def selected_test_ids(selection):
        """The id of every ticked row of a table of tests, as a plain list.

        `selection` is mo.ui.table's .value - a DataFrame of the selected
        rows, or None before anything is picked.
        """
        ids = []
        if selection is not None:
            for _, row in selection.iterrows():
                ids.append(int(row["id"]))
        return ids
    return (selected_test_ids,)


@app.cell
def _(mo):
    # Which test's chart is currently drawn. Separate from the table's
    # selection on purpose: selecting a row is cheap, drawing its chart
    # re-reads every raw sample it has from the database, so that only
    # happens when Show chart is actually clicked.
    get_shown_test_id, set_shown_test_id = mo.state(None)
    return get_shown_test_id, set_shown_test_id


@app.cell
def _(
    ANALYSIS_TAB,
    db_mod,
    db_selected_ids,
    get_box_values,
    load_to_analysis_btn,
    mo,
    set_active_tab,
    set_box_values,
    set_eval_mode,
    set_loaded_test,
    set_results_status_msg,
):
    # Bring the ticked saved test back into the Analysis tab, so it can be
    # re-evaluated and re-saved.
    if load_to_analysis_btn.value:
        _ids = db_selected_ids
        if len(_ids) == 1:
            _loaded = db_mod.load_test_for_analysis(_ids[0])
            if _loaded is None:
                set_results_status_msg(mo.callout(mo.md(f"Test #{_ids[0]} not found."), kind="warn"))
            else:
                set_loaded_test(_loaded)
                # Show the parameters the saved evaluation was made with, so
                # the boxes match what is on the chart. A test saved without
                # a filter shows 1, which is "filter off".
                if _loaded["filter_params"] is not None:
                    _filter_points = _loaded["filter_params"]["filter_points"]
                else:
                    _filter_points = "1"
                _previous_boxes = get_box_values()
                if _previous_boxes is None:
                    _generation = 1
                else:
                    _generation = _previous_boxes["generation"] + 1
                set_box_values({
                    "generation": _generation,
                    "filter_points": _filter_points,
                    "static_range": _loaded["eval_params"]["static_range"],
                    "dyn_min": _loaded["eval_params"]["dyn_min"],
                    "dyn_max": _loaded["eval_params"]["dyn_max"],
                })
                set_eval_mode("saved")
                set_active_tab(ANALYSIS_TAB)
                set_results_status_msg(mo.callout(mo.md(
                    f"Loaded test **#{_ids[0]}** (**{_loaded['file_name']}**) from the Database tab."
                    " Uploading a file and clicking Calculate goes back to the uploaded file."
                ), kind="info"))
    return


@app.cell
def _(db_selected_ids, set_shown_test_id, show_chart_btn):
    if show_chart_btn.value:
        if len(db_selected_ids) == 1:
            set_shown_test_id(db_selected_ids[0])
    return


# ── Charts ─────────────────────────────────────────────────────────────────
@app.cell
def _(charts, db_mod, get_shown_test_id, mo):
    # Deliberately depends on nothing but which test Show chart was clicked
    # for - NOT on the table's selection. Building this means re-reading
    # every raw sample of that test out of the database, so it has to happen
    # only when a different test is actually shown; if the table's selection
    # were a dependency here, merely ticking another row would rebuild the
    # whole figure from scratch.
    _shown = get_shown_test_id()
    if _shown is None:
        shown_chart = None
    else:
        _raw_table = db_mod.get_full_raw_table(_shown)
        _eval_table = db_mod.get_full_eval_table(_shown)
        _fig = charts.build_saved_test_figure(_raw_table, _eval_table)
        if _fig is None:
            shown_chart = mo.callout(mo.md("No raw signal saved for this test."), kind="info")
        else:
            # Same iframe wrapping as the live CoF Analysis chart, not
            # mo.ui.plotly directly: a saved test's figure is still built
            # from the full per-cycle marker tables, and mo.ui.plotly sends
            # the whole thing through marimo's own reactive output channel,
            # which enforces a size limit the raw HTML iframe below doesn't.
            shown_chart = mo.Html(charts.figure_to_zoom_iframe_html(_fig, zoom_key=f"saved-{_shown}"))
    return (shown_chart,)


@app.cell
def _(charts, db_mod, get_shown_test_id, mo):
    # Static and sliding friction against mean velocity, one point per step
    # (see charts.build_friction_velocity_figures). Built when Show chart is
    # clicked for a test, like the main chart above.
    _shown = get_shown_test_id()
    shown_velocity_charts = None
    if _shown is not None:
        _details = db_mod.get_test_details(_shown)
        _stroke = None
        if _details is not None:
            _stroke = _details["stroke_mm"]
        _title = ""
        for _t in db_mod.list_tests():
            if _t["id"] == _shown:
                _title = _t["file_name"].replace(".txt", "")
        _figures = charts.build_friction_velocity_figures(
            db_mod.get_step_results(_shown), _stroke, _title,
            all_steps=db_mod.get_step_df(_shown),
        )
        if _figures is None:
            shown_velocity_charts = mo.callout(mo.md(
                "No friction-velocity plots: this test has no step speeds (Drehzahl) saved."
            ), kind="info")
        else:
            _parts = [
                mo.Html('<p class="section-label" style="margin:0">FRICTION VS. VELOCITY (PER STEP, &plusmn; STD DEV)</p>'),
            ]
            if _stroke is None:
                _parts.append(mo.md(
                    "_The stroke of this test is not known, so the x axis is the speed in U/min. "
                    "Type the stroke (Hub Exzenter, e.g. 24) into **Stroke** above and click "
                    "**Save**, then tick the test and click **Show chart** again._"
                ))
            _parts.append(mo.ui.plotly(_figures[0]))
            _parts.append(mo.ui.plotly(_figures[1]))
            shown_velocity_charts = mo.vstack(_parts, gap=1)
    return (shown_velocity_charts,)


@app.cell
def _(db_mod, get_shown_test_id, mo, pipeline, results_table):
    # The per-step summary of a saved test: one row per step rather than one
    # per raw sample, so a test whose raw signal is hundreds of thousands of
    # rows lands here as a handful - small enough to render in the page.
    # Only results_table.SHOWN_COLUMNS are displayed; the raw Time/CoF/
    # Filtered CoF columns and the per-cycle/minima columns stay Excel-only
    # (Open in Excel still exports everything together).
    _shown = get_shown_test_id()
    if _shown is None:
        shown_eval_table = None
    else:
        _eval_df = results_table.shown_columns_only(db_mod.get_full_eval_table(_shown))
        if _eval_df is None or len(_eval_df) == 0:
            shown_eval_table = mo.callout(mo.md("No evaluated cycles saved for this test."), kind="info")
        else:
            _parts = [
                mo.ui.table(
                    _eval_df, selection=None,
                    pagination=False, show_column_summaries=False, show_data_types=False,
                ),
            ]
            # Below it: the same numbers split into CoF+ and CoF-, with the
            # Check against the per-step table, like on the Analysis tab.
            try:
                _pm = pipeline.add_check_column(
                    db_mod.get_plus_minus_df(_shown), db_mod.get_stats_df(_shown),
                )
                _pm_df = results_table.build_plus_minus_table(_pm)
                if _pm_df is not None:
                    _parts.append(mo.Html('<p class="section-label" style="margin:12px 0 0 0">CoF+ / CoF- (POSITIVE AND NEGATIVE STROKES)</p>'))
                    _parts.append(mo.ui.table(
                        _pm_df, selection=None,
                        pagination=False, show_column_summaries=False, show_data_types=False,
                    ))
            except Exception as _e:
                _parts.append(mo.callout(mo.md(f"**CoF+ / CoF- could not be shown:** {_e}"), kind="danger"))
            shown_eval_table = mo.vstack(_parts, gap=1)
    return (shown_eval_table,)


@app.cell
def _(df_display, speed_pulse, step_df, zero_crossings):
    # Nominal-speed square wave (30/Drehzahl s per half-stroke), anchored per
    # step on the first zero crossing Find zeros found there. Before Find
    # zeros it starts at each step's Startzeit instead, so it is visible as
    # soon as a file with steps is parsed. The found crossings also mark the
    # noisy steps (too many zeros in one stroke) that Evaluate with pulse
    # leaves out. The "Pulse offset" boxes live inside the chart iframe and
    # shift the trace in the browser only.
    if df_display is None:
        pulse = None
    else:
        pulse = speed_pulse.build_speed_pulse(df_display, step_df, zero_crossings)
    return (pulse,)


@app.cell
def _(active_filter_params, charts, cof_eval, df_display, df_proc, mo, parsed_file_id, pipeline, pulse, step_df, zero_crossings):
    if df_display is None:
        cof_chart = mo.Html(
            '<div style="height:360px;display:flex;align-items:center;justify-content:center;'
            'background:#fff;border-radius:8px;box-shadow:0 1px 4px rgba(0,0,0,0.08);color:#bbb;font-size:13px">'
            "Upload a file to see the chart</div>"
        )
    else:
        _filter_active = pipeline.is_filter_active(active_filter_params, df_proc)
        _fig = charts.build_cof_figure(
            df_display, df_proc, cof_eval, step_df, _filter_active,
            speed_pulse=pulse, zero_crossings=zero_crossings,
        )
        # df_display only ever gets built from data tagged with the file
        # that's actually in the upload box right now (see the df_display
        # cell above) - so this name is never stale, unlike just reading
        # file_upload directly here would risk if the two ever raced.
        _fname = parsed_file_id[0] if parsed_file_id else "&mdash;"
        cof_chart = mo.vstack([
            mo.Html(f'<p style="font-size:0.72rem;color:#888;margin:0 0 4px 0">'
                     f'Showing: <strong>{_fname}</strong></p>'),
            # Keyed by file, so the remembered x-zoom / y-range of one file
            # is never applied to the next one.
            mo.Html(charts.figure_to_zoom_iframe_html(_fig, zoom_key=f"live-{_fname}")),
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
def _(cof_eval, mo, plus_minus_error, plus_minus_result, results_table, stats_error, stats_result):
    # Same per-step summary table the Database tab shows for a saved test,
    # but for the file currently being worked on. Only
    # results_table.SHOWN_COLUMNS are displayed; the raw Time/CoF/Filtered
    # CoF columns and the per-cycle/minima columns stay Excel-only (Open
    # Results in Excel still exports everything together).
    _eval_df = results_table.shown_columns_only(
        results_table.build_eval_table(cof_eval, stats_result, stats_error)
    )
    if _eval_df is None or len(_eval_df) == 0:
        eval_table_panel = mo.Html("")
    else:
        _parts = [
            mo.Html('<p class="section-label" style="margin:0">EVALUATED CYCLES</p>'),
            mo.ui.table(
                _eval_df, selection=None,
                pagination=False, show_column_summaries=False, show_data_types=False,
            ),
        ]

        # Below it: the same numbers split into CoF+ and CoF-.
        _pm_df = results_table.build_plus_minus_table(plus_minus_result)
        if plus_minus_error is not None:
            _parts.append(mo.callout(mo.md(f"**CoF+ / CoF- could not be calculated:** {plus_minus_error}"), kind="danger"))
        elif _pm_df is not None:
            _parts.append(mo.Html('<p class="section-label" style="margin:12px 0 0 0">CoF+ / CoF- (POSITIVE AND NEGATIVE STROKES)</p>'))
            _parts.append(mo.md(
                "**CoF+** uses only the positive strokes, **CoF-** only the negative ones "
                "(shown as positive numbers). **CoF AVG** adds the two back together; "
                "**Check** says whether that matches the table above."
            ))
            _parts.append(mo.ui.table(
                _pm_df, selection=None,
                pagination=False, show_column_summaries=False, show_data_types=False,
            ))
        eval_table_panel = mo.vstack(_parts, gap=1)
    return (eval_table_panel,)


@app.cell
def _(
    active_filter_params,
    cof_eval,
    data_loader,
    df_display,
    df_proc,
    mo,
    pipeline,
    plus_minus_result,
    results_table,
    stats_error,
    stats_result,
    table_helpers,
):
    # A download (see open_excel_btn): the combined results table as a .csv,
    # only built when the button is clicked.
    def _build_results_csv():
        _filter_active = pipeline.is_filter_active(active_filter_params, df_proc)
        _df_raw_results = results_table.build_raw_table(df_display, df_proc, _filter_active)
        _df_eval_results = results_table.build_eval_table(cof_eval, stats_result, stats_error)
        if _df_eval_results is not None:
            _combined = table_helpers.combine_padded(_df_raw_results, _df_eval_results)
        else:
            _combined = _df_raw_results
        # The CoF+ / CoF- table goes in the columns to the right.
        _df_pm = results_table.build_plus_minus_export(plus_minus_result)
        if _df_pm is not None:
            _combined = table_helpers.combine_padded(_combined, _df_pm)
        return data_loader.dataframe_to_csv_bytes(_combined)

    open_results_excel_btn = mo.download(
        data=_build_results_csv,
        filename="results.csv",
        mimetype="text/csv",
        disabled=df_display is None,
        label="&#128194; Open Results in Excel",
    )
    return (open_results_excel_btn,)


@app.cell
def _(has_step_checkbox, mo, PANEL_STYLE, settings_store):
    # The Raw Data boxes are created in the same cell that lays them out.
    # marimo never re-runs the cell that created a UI element when that
    # element's value changes, so editing a box leaves this cell - and with
    # it the whole page, chart included - untouched. has_step_checkbox stays
    # a dependency on purpose: toggling it must rebuild the form to enable
    # or disable the step fields.
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
    # Three compact rows - one per group - laid out on ONE shared grid:
    # a fixed group-title column followed by six equal cells, each cell a
    # right-aligned label next to a narrow input. Same grid for every row,
    # so the inputs line up in straight columns across GENERAL / STEP DATA /
    # MAIN DATA. All values are small integers, hence the narrow inputs
    # (fixed-width wrapper div: marimo's text input is a shadow-DOM component
    # sized to its host, so a page-level CSS width can't reach it).
    _field = ('<div style="display:flex;align-items:center;gap:6px">'
              '<span style="font-size:0.78rem;color:#555;white-space:nowrap;width:104px;text-align:right">{label}</span>'
              '<div style="width:64px">{{{field}}}</div></div>')
    _group_open = ('<div style="display:grid;grid-template-columns:84px repeat(6, minmax(0, 1fr));align-items:center;gap:8px 4px">'
                   '<span class="section-label" style="margin:0;font-size:0.62rem;'
                   'font-weight:700;letter-spacing:1px;color:#999">{title}</span>')
    _group_close = '</div>'

    _raw_data_tpl = mo.Html(
        '<div style="display:flex;flex-direction:column;gap:10px">'
        + _group_open.format(title="GENERAL")
        + _field.format(label="Load correction", field="nlc")
        + _group_close
        + _group_open.format(title="STEP DATA")
        + _field.format(label="Start row", field="start_step_row")
        + _field.format(label="End row", field="end_step_row")
        + _field.format(label="Time col #", field="step_col_time")
        + _field.format(label="Drehzahl col #", field="step_col_speed")
        + _group_close
        + _group_open.format(title="MAIN DATA")
        + _field.format(label="Start row", field="start_main_row")
        + _field.format(label="Stop row (0 = end)", field="stop_main_row")
        + _field.format(label="Time col #", field="col_time")
        + _field.format(label="Friction L col #", field="col_left")
        + _field.format(label="Friction R col #", field="col_right")
        + _field.format(label="Normal load col #", field="col_load")
        + _group_close
        + '</div>'
    )
    raw_data_form = _raw_data_tpl.batch(
        nlc=mo.ui.text(value=_saved.get("nlc", ""), debounce=True),
        start_step_row=mo.ui.text(value=_saved.get("start_step_row", "0"), disabled=_step_fields_disabled, debounce=True),
        end_step_row=mo.ui.text(value=_saved.get("end_step_row", "0"), disabled=_step_fields_disabled, debounce=True),
        step_col_time=mo.ui.text(value=_saved.get("step_col_time", "1"), disabled=_step_fields_disabled, debounce=True),
        step_col_speed=mo.ui.text(value=_saved.get("step_col_speed", "0"), disabled=_step_fields_disabled, debounce=True),
        start_main_row=mo.ui.text(value=_saved.get("start_main_row", "41"), debounce=True),
        stop_main_row=mo.ui.text(value=_saved.get("stop_main_row", "0"), debounce=True),
        col_time=mo.ui.text(value=_saved.get("col_time", "1"), debounce=True),
        col_left=mo.ui.text(value=_saved.get("col_left", "13"), debounce=True),
        col_right=mo.ui.text(value=_saved.get("col_right", "14"), debounce=True),
        col_load=mo.ui.text(value=_saved.get("col_load", "3"), debounce=True),
    )

    # Title and the "Has step data" checkbox share one line; the form
    # itself is three compact rows below.
    raw_data_card = mo.vstack([
        mo.hstack([
            mo.Html('<p class="panel-title" style="margin:0">Raw Data</p>'),
            has_step_checkbox,
        ], justify="space-between", align="center"),
        raw_data_form,
    ], gap=1).style(PANEL_STYLE)
    return raw_data_card, raw_data_form


@app.cell
def _(mo):
    # Everything in this cell is created here AND laid out here: marimo
    # never re-runs the cell that created a UI element when its value
    # changes, so neither typing in a box nor clicking Filter/Evaluate
    # rebuilds this row - the page and the chart are left alone, and the
    # boxes keep what was typed. The Offset button and its badge live in
    # the next cell because the badge has to read the offset state, and
    # reading it here would rebuild these boxes on every Offset click.
    #
    # get_box_values is the one thing that may rebuild this cell: it changes
    # only when a saved test is loaded from the Database tab, and then the boxes are
    # supposed to show that test's parameters.
    filter_btn = mo.ui.run_button(label="Filter")
    find_zeros_btn = mo.ui.run_button(label="Find zeros")
    # Fixed-width wrapper around each placeholder: marimo's text input is a
    # shadow-DOM web component sized at 100% of its host element, so a
    # page-level <style> width rule can never reach it — this is the only
    # way to control its rendered width.
    _filter_tpl = mo.Html(
        '<div style="display:flex;align-items:center;gap:16px">'
        '<div style="display:flex;align-items:center;gap:6px">'
        '<span style="font-size:0.82rem;color:#444;white-space:nowrap">Filter pts</span>'
        '<div style="width:60px">{filter_points}</div></div>'
        '</div>'
    )
    filter_fields = _filter_tpl.batch(
        filter_points=mo.ui.text(value="25", debounce=True),
    )

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
        static_range=mo.ui.text(value="10.0", debounce=True),
        dyn_min=mo.ui.text(value="20.0", debounce=True),
        dyn_max=mo.ui.text(value="80.0", debounce=True),
    )

    def _rule():
        return mo.Html('<div style="width:1px;height:28px;background:#e3e6ea;margin:0 6px"></div>')

    controls_row = mo.hstack([
        filter_fields, filter_btn,
        _rule(),
        eval_fields, find_zeros_btn,
    ], gap=1, align="center", justify="start", wrap=True)
    return controls_row, eval_fields, filter_btn, filter_fields, find_zeros_btn


@app.cell
def _(TOOLBAR_STYLE, controls_row, get_offset, mo, offset_btn):
    # One slim toolbar instead of three half-empty cards: the controls read
    # left to right in the order they are used - Offset, Filter, Evaluate -
    # with a thin vertical rule between the groups.
    if get_offset():
        _offset_badge = mo.Html(
            '<span style="font-size:0.68rem;font-weight:700;letter-spacing:.5px;color:#fff;'
            'background:#4cceac;border-radius:10px;padding:2px 8px">ON</span>'
        )
    else:
        _offset_badge = mo.Html(
            '<span style="font-size:0.68rem;font-weight:700;letter-spacing:.5px;color:#999;'
            'background:#eef1f4;border-radius:10px;padding:2px 8px">OFF</span>'
        )
    _rule = mo.Html('<div style="width:1px;height:28px;background:#e3e6ea;margin:0 6px"></div>')

    actions_row = mo.hstack([
        offset_btn, _offset_badge,
        _rule,
        controls_row,
    ], gap=1, align="center", justify="start", wrap=True).style(TOOLBAR_STYLE)
    return (actions_row,)


@app.cell
def _(get_box_values, mo):
    # Puts the loaded test's parameters into the Filter / Evaluate boxes.
    #
    # Not by re-creating the boxes with new values: the browser keeps the
    # text of a box it has already drawn, so that shows up a load too late.
    # Instead a hidden iframe writes the values into them the way the chart
    # writes the pulse offsets - through marimo's own "marimo-value-input"
    # event, which updates both what is on screen and the value Python
    # sees. The script runs again on every load because the values change
    # with it, and it retries for a moment in case the toolbar is rendered
    # after it.
    _values = get_box_values()
    if _values is None:
        box_value_pusher = mo.Html("")
    else:
        _pairs = [
            ("Filter pts", _values["filter_points"]),
            ("Static %", _values["static_range"]),
            ("Dyn min %", _values["dyn_min"]),
            ("Dyn max %", _values["dyn_max"]),
        ]
        _wanted = ", ".join('["%s", "%s"]' % (_label, _value) for _label, _value in _pairs)
        _script = (
            "<html><body><script>"
            "var WANTED = [" + _wanted + "];"
            "var GENERATION = " + str(_values["generation"]) + ";"
            "var tries = 0;"
            "function push() {"
            "  var doc; try { doc = window.parent.document; } catch (e) { return; }"
            "  var done = 0;"
            "  for (var i = 0; i < WANTED.length; i++) {"
            "    var label = WANTED[i][0], value = WANTED[i][1];"
            "    var spans = doc.querySelectorAll('span');"
            "    for (var j = 0; j < spans.length; j++) {"
            "      if (spans[j].textContent.trim() !== label) { continue; }"
            "      var holder = spans[j].nextElementSibling;"
            "      var el = holder ? holder.querySelector('marimo-text') : null;"
            "      if (!el) { continue; }"
            "      doc.dispatchEvent(new window.parent.CustomEvent('marimo-value-input', {"
            "        bubbles: true, composed: true, detail: { value: value, element: el }"
            "      }));"
            "      done++;"
            "      break;"
            "    }"
            "  }"
            "  tries++;"
            "  if (done < WANTED.length && tries < 20) { setTimeout(push, 200); }"
            "}"
            "setTimeout(push, 100);"
            "</script></body></html>"
        )
        _srcdoc = _script.replace("&", "&amp;").replace("<", "&lt;").replace("'", "&#39;")
        box_value_pusher = mo.Html(
            "<iframe srcdoc='" + _srcdoc + "' style='width:0;height:0;border:none;display:block'></iframe>"
        )
    return (box_value_pusher,)


# ── Database ───────────────────────────────────────────────────────────────
@app.cell
def _(mo):
    # The Database tab's one message box, and the delete waiting for a
    # "Yes, delete": {"kind": "test", "ids": [...], "name": ...} or
    # {"kind": "column", "id": ..., "name": ...}.
    get_db_msg, set_db_msg = mo.state(None)
    get_db_pending, set_db_pending = mo.state(None)
    return get_db_msg, get_db_pending, set_db_msg, set_db_pending


@app.cell
def _(mo, set_db_msg, set_db_pending):
    # The jobs of this tab, shown one at a time. Never rebuilt, so the choice
    # stays while tests are changed.
    def _view_changed(_value):
        # A message or question belongs to the view it came from.
        set_db_msg(None)
        set_db_pending(None)

    db_view = mo.ui.radio(
        options={"Tests": "tests", "Manage columns": "columns"},
        value="Tests",
        inline=True,
        label="What do you want to do?",
        on_change=_view_changed,
    )
    return (db_view,)


@app.cell
def _(mo):
    db_confirm_btn = mo.ui.run_button(label="Yes, delete", kind="danger")
    db_cancel_btn = mo.ui.run_button(label="Cancel")
    return db_cancel_btn, db_confirm_btn


@app.cell
def _(SUB_PANEL_STYLE, form_rows_html, get_columns_version, mo):
    # Rebuilt after a column was added, renamed or deleted, which also
    # empties the boxes for the next one. The boxes are created AND laid out
    # here, so typing in them never re-runs anything else (see db_fill_form).
    get_columns_version()
    db_new_column_name = mo.ui.text(full_width=True)
    db_new_column_unit = mo.ui.text(placeholder="e.g. mm, leave empty if it has none", full_width=True)
    db_new_column_kind = mo.ui.dropdown(
        options={"Text": "text", "Number": "number"}, value="Text", full_width=True,
    )
    db_add_column_btn = mo.ui.run_button(label="Add column")
    _rows = [
        ("Name", db_new_column_name, ""),
        ("Unit", db_new_column_unit, ""),
        ("Type", db_new_column_kind, ""),
    ]
    database_add_column_panel = mo.vstack([
        mo.md("**Add a column**"),
        mo.Html(form_rows_html(_rows)),
        mo.hstack([db_add_column_btn], justify="start"),
    ], gap=1).style(SUB_PANEL_STYLE)
    return (
        database_add_column_panel,
        db_add_column_btn,
        db_new_column_kind,
        db_new_column_name,
        db_new_column_unit,
    )


@app.cell
def _(db_mod, get_columns_version, mo):
    get_columns_version()
    _column_options = {}
    for _column in db_mod.list_info_columns():
        if not _column["protected"]:
            _column_options[_column["label"]] = _column["id"]
    db_column_select = mo.ui.dropdown(options=_column_options, full_width=True)
    return (db_column_select,)


@app.cell
def _(SUB_PANEL_STYLE, db_column_select, db_mod, form_rows_html, mo):
    # Rebuilt for each chosen column, so the boxes start with its name and
    # unit. They only show once a column is chosen.
    _name = ""
    _unit = ""
    for _column in db_mod.list_info_columns():
        if _column["id"] == db_column_select.value:
            _name = _column["name"]
            _unit = _column["unit"]
    db_rename_name = mo.ui.text(value=_name, full_width=True)
    db_rename_unit = mo.ui.text(value=_unit, full_width=True)
    db_rename_btn = mo.ui.run_button(label="Rename")
    db_delete_column_btn = mo.ui.run_button(label="&#128465; Delete", kind="danger")
    _title = mo.md("**Rename or delete a column**")
    if db_column_select.value is None:
        database_change_column_panel = mo.vstack([
            _title,
            mo.Html(form_rows_html([("Column", db_column_select, "")])),
            mo.md("Choose a column to rename or delete it."),
        ], gap=1).style(SUB_PANEL_STYLE)
    else:
        _rows = [
            ("Column", db_column_select, ""),
            ("Name", db_rename_name, ""),
            ("Unit", db_rename_unit, ""),
        ]
        database_change_column_panel = mo.vstack([
            _title,
            mo.Html(form_rows_html(_rows)),
            mo.hstack([db_rename_btn, db_delete_column_btn], justify="start", gap=1),
            mo.md("A new unit does not convert the numbers already typed in."),
        ], gap=1).style(SUB_PANEL_STYLE)
    return (
        database_change_column_panel,
        db_delete_column_btn,
        db_rename_btn,
        db_rename_name,
        db_rename_unit,
    )


@app.cell
def _(
    get_active_tab,
    get_batch_log,
    get_columns_version,
    get_database_version,
    get_tests_version,
    info_fields,
    mo,
):
    # The stored tests, read again whenever this tab is opened or something
    # changed them. Ticking rows changes nothing here, so it doesn't rebuild
    # the table and lose the ticks.
    get_active_tab()
    get_batch_log()
    get_tests_version()
    get_columns_version()
    get_database_version()

    _table = info_fields.build_database_table()
    db_tests_table = mo.ui.table(
        _table, selection="multi", page_size=12, show_column_summaries=False, show_data_types=False,
    )

    _n_empty = 0
    if len(_table) > 0:
        _n_empty = int(_table["Empty fields"].sum())
    database_tests_panel = mo.vstack([
        mo.md(f"**{len(_table)}** tests, **{_n_empty}** empty fields."),
        db_tests_table,
    ], gap=1)
    return database_tests_panel, db_tests_table


@app.cell
def _(db_tests_table, selected_test_ids):
    db_selected_ids = selected_test_ids(db_tests_table.value)
    db_selected_name = f"{len(db_selected_ids)} tests"
    if len(db_selected_ids) == 1:
        db_selected_name = f"#{db_selected_ids[0]}  {db_tests_table.value.iloc[0]['File name']}"
    return db_selected_ids, db_selected_name


@app.cell
def _(data_loader, db_mod, db_selected_ids, mo, results_table, table_helpers):
    # What is saved of the one ticked test, and its "Open in Excel" button.
    db_excel_download = None
    db_saved_data_text = ""
    if len(db_selected_ids) == 1:
        _test_id = db_selected_ids[0]
        _n_raw = db_mod.count_raw_samples(_test_id)
        _n_eval = db_mod.count_cycles(_test_id)
        if _n_raw == 0 and _n_eval == 0:
            db_saved_data_text = "No saved data for this test."
        else:
            db_saved_data_text = f"{_n_raw:,} raw samples, {_n_eval:,} evaluated cycles."

            # A download (see open_excel_btn), only built when clicked.
            def _build_test_csv():
                _raw_table = db_mod.get_full_raw_table(_test_id)
                _eval_table = db_mod.get_full_eval_table(_test_id)
                _combined = table_helpers.combine_padded(_raw_table, _eval_table)
                # The CoF+ / CoF- table goes in the columns to the right.
                _pm_table = results_table.build_plus_minus_export(db_mod.get_plus_minus_df(_test_id))
                if _pm_table is not None:
                    _combined = table_helpers.combine_padded(_combined, _pm_table)
                return data_loader.dataframe_to_csv_bytes(_combined)

            db_excel_download = mo.download(
                data=_build_test_csv,
                filename=f"test_{_test_id}_results.csv",
                mimetype="text/csv",
                label="&#128194; Open in Excel",
            )
    return db_excel_download, db_saved_data_text


@app.cell
def _(
    build_info_form,
    db_excel_download,
    db_mod,
    db_saved_data_text,
    db_selected_ids,
    db_selected_name,
    mo,
    summary_download,
):
    # The form for the ticked tests. Created AND laid out here: marimo re-runs
    # every cell that uses a box when its value changes, but never the cell
    # that created it. If another cell placed the form on the page, each
    # keystroke would re-run that cell, rebuild the tab and throw away what
    # was just typed. Other cells only get database_fill_panel, which is
    # plain layout, not a box. Ticking other tests starts the form again.
    _values = {}
    if len(db_selected_ids) == 1:
        _values = db_mod.get_info_values(db_selected_ids[0])
    db_fill_form = build_info_form(db_mod.list_info_columns(), _values)
    db_save_btn = mo.ui.run_button(label="&#128190; Save")
    db_delete_test_btn = mo.ui.run_button(label="&#128465; Delete", kind="danger")
    show_chart_btn = mo.ui.run_button(label="&#128200; Show chart")
    load_to_analysis_btn = mo.ui.run_button(label="&#128202; Load into Analysis")

    if len(db_selected_ids) == 0:
        database_fill_panel = mo.md(
            "**Tick one or more tests** in the table to fill them in, see their results or delete them."
        )
    else:
        _buttons = [db_save_btn]
        if len(db_selected_ids) == 1:
            _title = f"**Test {db_selected_name}**  \n{db_saved_data_text}"
            _buttons.append(show_chart_btn)
            _buttons.append(load_to_analysis_btn)
            if db_excel_download is not None:
                _buttons.append(db_excel_download)
        else:
            _title = (
                f"**{db_selected_name} ticked.** Only the boxes you fill in are saved, "
                "the others keep each test's own value."
            )
        _buttons.append(summary_download)
        _buttons.append(db_delete_test_btn)
        database_fill_panel = mo.vstack([
            mo.md(_title),
            db_fill_form,
            mo.hstack(_buttons, justify="start", align="center", gap=1, wrap=True),
        ], gap=1)
    return (
        database_fill_panel,
        db_delete_test_btn,
        db_fill_form,
        db_save_btn,
        load_to_analysis_btn,
        show_chart_btn,
    )


@app.cell
def _(
    db_selected_ids,
    db_selected_name,
    get_shown_test_id,
    mo,
    shown_chart,
    shown_eval_table,
    shown_velocity_charts,
):
    # Cheap: only places the already-built chart and tables. They show while
    # their own test is the one ticked, and hide (without being thrown away)
    # as soon as the ticks are anything else - so ticking it again brings
    # them straight back with no database read.
    _shown = get_shown_test_id()
    database_results_panel = None
    if _shown is not None and db_selected_ids == [_shown]:
        database_results_panel = mo.vstack([
            mo.md(f"**Results of test {db_selected_name}**"),
            shown_chart,
            mo.Html('<hr class="divider">'),
            mo.Html('<p class="section-label" style="margin:0">EVALUATED CYCLES</p>'),
            shown_eval_table,
            shown_velocity_charts,
        ], gap=1)
    return (database_results_panel,)


@app.cell
def _(
    get_active_tab,
    get_batch_log,
    get_columns_version,
    get_database_version,
    get_tests_version,
    info_fields,
    mo,
):
    get_active_tab()
    get_batch_log()
    get_tests_version()
    get_columns_version()
    get_database_version()
    database_columns_table = mo.ui.table(
        info_fields.build_column_table(), selection=None, pagination=False,
        show_column_summaries=False, show_data_types=False, show_download=False,
    )
    return (database_columns_table,)


@app.cell
def _(db_fill_form, db_save_btn, db_selected_ids, get_database_version, info_fields, mo, set_database_version, set_db_msg):
    if db_save_btn.value:
        try:
            _n_saved, _problems = info_fields.save_typed_values(db_selected_ids, db_fill_form.value)
            if len(_problems) > 0:
                set_db_msg(mo.callout(mo.md("**Not saved:** " + "; ".join(_problems) + "."), kind="warn"))
            else:
                set_db_msg(mo.callout(mo.md(f"Saved. Tests changed: **{_n_saved}**."), kind="success"))
                set_database_version(get_database_version() + 1)
        except Exception as _e:
            set_db_msg(mo.callout(mo.md(f"**Save failed:** {_e}"), kind="danger"))
    return


@app.cell
def _(
    db_add_column_btn,
    db_mod,
    db_new_column_kind,
    db_new_column_name,
    db_new_column_unit,
    get_columns_version,
    mo,
    set_columns_version,
    set_db_msg,
):
    if db_add_column_btn.value:
        try:
            _label = db_mod.add_info_column(
                db_new_column_name.value, db_new_column_kind.value, db_new_column_unit.value,
            )
            set_db_msg(mo.callout(mo.md(f"Added the column **{_label}**."), kind="success"))
            set_columns_version(get_columns_version() + 1)
        except ValueError as _e:
            set_db_msg(mo.callout(mo.md(f"**Column not added:** {_e}."), kind="warn"))
    return


@app.cell
def _(db_column_select, db_mod, db_rename_btn, db_rename_name, db_rename_unit, get_columns_version, mo, set_columns_version, set_db_msg):
    if db_rename_btn.value:
        try:
            _label = db_mod.rename_info_column(
                db_column_select.value, db_rename_name.value, db_rename_unit.value,
            )
            set_db_msg(mo.callout(mo.md(f"The column is now called **{_label}**."), kind="success"))
            set_columns_version(get_columns_version() + 1)
        except ValueError as _e:
            set_db_msg(mo.callout(mo.md(f"**Not renamed:** {_e}."), kind="warn"))
    return


@app.cell
def _(db_column_select, db_delete_column_btn, db_delete_test_btn, db_selected_ids, db_selected_name, set_db_msg, set_db_pending):
    # A delete can't be undone, so these two buttons only ask.
    if db_delete_test_btn.value:
        set_db_msg(None)
        set_db_pending({"kind": "test", "ids": db_selected_ids, "name": db_selected_name})
    if db_delete_column_btn.value:
        set_db_msg(None)
        set_db_pending({"kind": "column", "id": db_column_select.value, "name": db_column_select.selected_key})
    return


@app.cell
def _(
    db_cancel_btn,
    db_confirm_btn,
    db_mod,
    get_columns_version,
    get_database_version,
    get_db_pending,
    get_shown_test_id,
    mo,
    set_columns_version,
    set_database_version,
    set_db_msg,
    set_db_pending,
    set_shown_test_id,
):
    if db_cancel_btn.value:
        set_db_pending(None)
    if db_confirm_btn.value and get_db_pending() is not None:
        _pending = get_db_pending()
        set_db_pending(None)
        try:
            if _pending["kind"] == "test":
                for _test_id in _pending["ids"]:
                    db_mod.delete_test(_test_id)
                    if get_shown_test_id() == _test_id:
                        set_shown_test_id(None)
                set_db_msg(mo.callout(mo.md(f"Deleted **{_pending['name']}**."), kind="success"))
                set_database_version(get_database_version() + 1)
            else:
                db_mod.delete_info_column(_pending["id"])
                set_db_msg(mo.callout(mo.md(f"Deleted the column **{_pending['name']}**."), kind="success"))
                set_columns_version(get_columns_version() + 1)
        except Exception as _e:
            set_db_msg(mo.callout(mo.md(f"**Not deleted:** {_e}"), kind="danger"))
    return


@app.cell
def _(
    PANEL_STYLE,
    database_add_column_panel,
    database_change_column_panel,
    database_columns_table,
    database_fill_panel,
    database_results_panel,
    database_tests_panel,
    db_cancel_btn,
    db_confirm_btn,
    db_view,
    get_db_msg,
    get_db_pending,
    mo,
):
    # A question or message always comes right under the buttons that asked
    # for it, above any long table: with the answer far from the button, a
    # click seemed to do nothing.
    _answers = []
    _pending = get_db_pending()
    if _pending is not None:
        if _pending["kind"] == "test":
            _question = (
                f"Delete **{_pending['name']}** with all the stored data? "
                "This can't be undone."
            )
        else:
            _question = (
                f"Delete the column **{_pending['name']}** and its values in every test? "
                "This can't be undone."
            )
        _answers.append(mo.callout(mo.vstack([
            mo.md(_question),
            mo.hstack([db_confirm_btn, db_cancel_btn], justify="start", gap=1),
        ], gap=1), kind="warn"))
    if get_db_msg() is not None:
        _answers.append(get_db_msg())

    # Only the chosen view goes into the page.
    if db_view.value == "tests":
        if database_results_panel is not None:
            _answers.append(mo.md("The chart and results are **under the table**."))
        _parts = [database_fill_panel] + _answers + [database_tests_panel]
        if database_results_panel is not None:
            _parts.append(mo.Html('<hr class="divider">'))
            _parts.append(database_results_panel)
    else:
        _parts = [mo.hstack(
            [database_add_column_panel, database_change_column_panel],
            widths="equal", align="stretch", gap=2,
        )]
        _parts = _parts + _answers + [
            mo.md("**All columns**"),
            database_columns_table,
        ]
    database_tab = mo.vstack([
        mo.vstack([db_view, mo.Html('<hr class="divider">')] + _parts, gap=2).style(PANEL_STYLE),
    ], gap=2).style({"padding": "20px 0"})
    return (database_tab,)


# ── Batch (whole folder) ───────────────────────────────────────────────────
@app.cell
def _(mo):
    # Created and never rebuilt (no dependencies), so the uploaded files
    # stay. An upload (not a folder browser), so the files come from the
    # user's own computer even when the app runs as a server on another PC.
    batch_folder = mo.ui.file(
        filetypes=[".txt"],
        multiple=True,
        kind="area",
        max_size=1_000_000_000,
        label="Drag the folder (or its .txt files) here, or click to pick the files",
    )
    batch_run_btn = mo.ui.run_button(label="&#9654; Run files")
    batch_overwrite_btn = mo.ui.run_button(label="Overwrite them", kind="danger")
    batch_skip_btn = mo.ui.run_button(label="Skip them")
    return batch_folder, batch_overwrite_btn, batch_run_btn, batch_skip_btn


@app.cell
def _(mo):
    # The batch waiting for the overwrite question to be answered (None when
    # nothing is waiting), and the result rows of the last batch run.
    get_batch_plan, set_batch_plan = mo.state(None)
    get_batch_log, set_batch_log = mo.state(None)
    get_batch_msg, set_batch_msg = mo.state(None)
    return get_batch_log, get_batch_msg, get_batch_plan, set_batch_log, set_batch_msg, set_batch_plan


@app.cell
def _(batch, mo, set_batch_log):
    def run_batch(plan, overwrite):
        """Evaluate and save every file of `plan`, one after another, with a
        progress bar. Files already saved are overwritten when `overwrite`
        is True, otherwise skipped."""
        _rows = []
        _files = plan["files"]
        with mo.status.progress_bar(total=len(_files), title="Evaluating files", remove_on_exit=True) as _bar:
            for _name in _files:
                _bar.update(increment=0, subtitle=_name)
                _rows.append(batch.run_one(plan, _name, overwrite))
                _bar.update()
        set_batch_log(_rows)
    return (run_batch,)


@app.cell
def _(
    batch,
    batch_folder,
    batch_run_btn,
    eval_fields,
    filter_fields,
    has_step_checkbox,
    mo,
    raw_data_form,
    run_batch,
    set_batch_log,
    set_batch_msg,
    set_batch_plan,
):
    # "Run files": take the settings as they are right now, look at the
    # uploaded files, and either ask about files that are already saved or
    # start.
    if batch_run_btn.value:
        set_batch_plan(None)
        if not batch_folder.value:
            set_batch_msg(mo.callout(mo.md("Upload the test files first."), kind="warn"))
        else:
            _raw_params = dict(raw_data_form.value)
            _raw_params["has_step"] = has_step_checkbox.value
            _plan = batch.make_plan(
                batch_folder.value, _raw_params,
                dict(filter_fields.value), dict(eval_fields.value),
            )
            if len(_plan["files"]) == 0:
                set_batch_msg(mo.callout(mo.md("No .txt files among the uploaded files."), kind="warn"))
            elif len(_plan["existing"]) > 0:
                set_batch_plan(_plan)
                set_batch_msg(None)
            else:
                set_batch_log(None)
                set_batch_msg(None)
                run_batch(_plan, overwrite=False)
                set_batch_msg(mo.callout(mo.md(f"Done: **{len(_plan['files'])}** files."), kind="success"))
    return


@app.cell
def _(batch_overwrite_btn, batch_skip_btn, get_batch_plan, mo, run_batch, set_batch_log, set_batch_msg, set_batch_plan):
    # The answer to "these files are already saved - overwrite them?".
    if batch_overwrite_btn.value or batch_skip_btn.value:
        _plan = get_batch_plan()
        if _plan is not None:
            set_batch_plan(None)
            set_batch_log(None)
            run_batch(_plan, overwrite=batch_overwrite_btn.value)
            set_batch_msg(mo.callout(mo.md(f"Done: **{len(_plan['files'])}** files."), kind="success"))
    return


@app.cell
def _(
    PANEL_STYLE,
    batch_folder,
    batch_overwrite_btn,
    batch_run_btn,
    batch_skip_btn,
    get_batch_log,
    get_batch_msg,
    get_batch_plan,
    mo,
):
    import pandas as _pd

    _parts = [
        mo.Html('<p class="panel-title">Evaluate a whole folder</p>'),
        mo.md(
            "Every uploaded `.txt` file goes through **Offset &rarr; Filter &rarr; "
            "Find zeros &rarr; Evaluate with pulse &rarr; Save**, one after another. "
            "Uses the **Raw Data** settings and the **Filter pts / Static % / Dyn min % / "
            "Dyn max %** boxes from the Analysis tab, with pulse offset 0 ms. "
            "The information about each test can be filled in afterwards on the "
            "**Database** tab."
        ),
        batch_folder,
        batch_run_btn,
    ]

    _plan = get_batch_plan()
    if _plan is not None:
        _parts.append(mo.callout(mo.vstack([
            mo.md(
                f"**{len(_plan['existing'])}** of the {len(_plan['files'])} files are already saved: "
                + ", ".join(_plan["existing"])
                + ". Do you want to overwrite them?"
            ),
            mo.hstack([batch_overwrite_btn, batch_skip_btn], justify="start", gap=1),
        ], gap=1), kind="warn"))

    if get_batch_msg() is not None:
        _parts.append(get_batch_msg())

    _log = get_batch_log()
    if _log is not None:
        _parts.append(mo.ui.table(
            _pd.DataFrame(_log), selection=None,
            pagination=False, show_column_summaries=False, show_data_types=False,
        ))

    batch_tab = mo.vstack([
        mo.vstack(_parts, gap=2).style(PANEL_STYLE),
    ]).style({"padding": "20px 0"})
    return (batch_tab,)


# ── AI (train a model, predict) ────────────────────────────────────────────
@app.cell
def _(ai_model, mo):
    # The trained model (a plain dict, see ai_model.py), starting with the
    # one saved last time; the latest AI message; and the latest prediction.
    get_ai_model, set_ai_model = mo.state(ai_model.load_model())
    get_ai_msg, set_ai_msg = mo.state(None)
    get_ai_prediction, set_ai_prediction = mo.state(None)
    return get_ai_model, get_ai_msg, get_ai_prediction, set_ai_model, set_ai_msg, set_ai_prediction


@app.cell
def _(mo):
    # Own cell with no dependencies, so this button is never rebuilt.
    ai_reload_btn = mo.ui.run_button(label="&#128260; Reload tests")
    return (ai_reload_btn,)


@app.cell
def _(ai_model, ai_reload_btn, db_mod, get_batch_log, get_columns_version, get_database_version, mo):
    # The data table: one row per saved test. Tick "use" for the tests the
    # model should learn from, and type in their temperature, humidity and
    # material. Re-read from the database on Reload and after a batch run.
    #
    # The table, the parameter choice and the buttons are created AND laid
    # out in this cell: marimo re-runs every cell that uses an element when
    # its value changes, except the cell that created it. So typing in the
    # table never rebuilds the table and throws the typing away.
    ai_reload_btn.value
    get_batch_log()
    get_columns_version()
    get_database_version()

    import pandas as _pd

    # A column deleted on the Database tab is not offered here either.
    _deleted = db_mod.deleted_info_fields()

    _tests = db_mod.list_tests_df()
    _rows = []
    for _i in range(len(_tests)):
        _t = _tests.iloc[_i]
        _material = _t["material"]
        if _material is None or str(_material).lower() == "nan":
            _material = ""
        _rows.append({
            "use": True,
            "id": int(_t["id"]),
            "file_name": _t["file_name"],
            "temperature": ai_model.to_number(_t["temperature"]),
            "humidity": ai_model.to_number(_t["humidity"]),
            "material": _material,
            "stroke_mm": ai_model.to_number(_t["stroke_mm"]),
        })
    _table = _pd.DataFrame(_rows, columns=["use", "id", "file_name", "temperature", "humidity", "material", "stroke_mm"])
    _table = _table.drop(columns=_deleted)

    _editable = ["use"]
    for _name in ["temperature", "humidity", "material", "stroke_mm"]:
        if _name not in _deleted:
            _editable.append(_name)
    ai_data_editor = mo.ui.data_editor(
        _table,
        editable_columns=_editable,
        pagination=False,
    )
    # marimo shows the dict's keys and gives back its values: so the keys
    # are the readable labels and the values the names ai_model uses.
    _feature_choices = {}
    for _name in ai_model.ALL_FEATURES:
        if _name not in _deleted:
            _feature_choices[ai_model.FEATURE_LABELS[_name]] = _name
    ai_features = mo.ui.multiselect(
        options=_feature_choices,
        value=list(_feature_choices.keys()),
        label="Input parameters for the model",
    )
    ai_save_btn = mo.ui.run_button(label="&#128190; Save parameters")
    ai_train_btn = mo.ui.run_button(label="&#129504; Train model")

    ai_data_panel = mo.vstack([
        mo.Html('<p class="panel-title">1. Data: choose the tests and type in their parameters</p>'),
        mo.md(
            "Tick **use** for the tests the model should learn from, and fill in "
            "**temperature [&deg;C]**, **humidity [%]** and **material** "
            "(**stroke_mm** is filled in from the file when a test is saved). Each evaluated "
            "step of a test is one example: its speed and whether the speed is going up or "
            "down come from the file, and a step counts more the more cycles it has. "
            "Skipped steps, and tests with an empty parameter, are left out."
        ),
        ai_data_editor,
        mo.hstack([ai_reload_btn, ai_save_btn], justify="start", gap=2),
        mo.Html('<hr class="divider">'),
        mo.Html('<p class="panel-title">2. Train</p>'),
        mo.hstack([ai_features, ai_train_btn], justify="start", align="end", gap=2, wrap=True),
    ], gap=2)
    return ai_data_editor, ai_data_panel, ai_features, ai_save_btn, ai_train_btn


@app.cell
def _(ai_model, db_mod):
    def save_ai_parameters(edited_table):
        """Store the typed-in temperature / humidity / material / stroke of
        every row of the data table on its saved test. The test's note is kept.
        Returns how many tests were updated."""
        import pandas as _pd
        _table = _pd.DataFrame(edited_table)
        _count = 0
        for _i in range(len(_table)):
            _row = _table.iloc[_i]
            _test_id = int(_row["id"])
            _details = db_mod.get_test_details(_test_id)
            if _details is None:
                continue
            if "material" in _table.columns:
                _material = _row["material"]
                if _material is None or str(_material).strip() == "" or str(_material).lower() == "nan":
                    _material = None
                else:
                    _material = str(_material).strip()
                _details["material"] = _material
            if "temperature" in _table.columns:
                _details["temperature"] = ai_model.to_number(_row["temperature"])
            if "humidity" in _table.columns:
                _details["humidity"] = ai_model.to_number(_row["humidity"])
            if "stroke_mm" in _table.columns:
                _details["stroke_mm"] = ai_model.to_number(_row["stroke_mm"])
            db_mod.save_test_details(_test_id, _details)
            _count = _count + 1
        return _count
    return (save_ai_parameters,)


@app.cell
def _(ai_data_editor, ai_save_btn, mo, save_ai_parameters, set_ai_msg):
    if ai_save_btn.value:
        try:
            _n = save_ai_parameters(ai_data_editor.value)
            set_ai_msg(mo.callout(mo.md(f"Saved the parameters of **{_n}** tests."), kind="success"))
        except Exception as _e:
            set_ai_msg(mo.callout(mo.md(f"**Could not save the parameters:** {_e}"), kind="danger"))
    return


@app.cell
def _(
    ai_data_editor,
    ai_features,
    ai_model,
    ai_train_btn,
    mo,
    save_ai_parameters,
    set_ai_model,
    set_ai_msg,
    set_ai_prediction,
):
    # "Train model": save the typed-in parameters first (so the model and
    # the database agree), then learn from the ticked tests.
    if ai_train_btn.value:
        try:
            save_ai_parameters(ai_data_editor.value)
            import pandas as _pd
            _table = _pd.DataFrame(ai_data_editor.value)
            _ids = []
            for _i in range(len(_table)):
                if bool(_table.iloc[_i]["use"]):
                    _ids.append(int(_table.iloc[_i]["id"]))
            if len(_ids) == 0:
                raise ValueError("tick **use** for at least one test")
            # Keep the parameters in the fixed order of ai_model.ALL_FEATURES.
            _features = []
            for _name in ai_model.ALL_FEATURES:
                if _name in ai_features.value:
                    _features.append(_name)
            _training = ai_model.build_training_table(_ids)
            _model = ai_model.train(_training, _features)
            ai_model.save_model(_model)
            set_ai_model(_model)
            set_ai_prediction(None)
            set_ai_msg(mo.callout(mo.md(
                f"Trained on **{_model['n_rows']}** steps from **{_model['n_tests']}** tests "
                f"({_model['n_rows_left_out']} steps left out because a parameter was missing)."
            ), kind="success"))
        except ValueError as _e:
            set_ai_msg(mo.callout(mo.md(f"**Not trained:** {_e}"), kind="warn"))
        except Exception as _e:
            set_ai_msg(mo.callout(mo.md(f"**Training failed:** {_e}"), kind="danger"))
    return


@app.cell
def _(ai_model, get_ai_model, mo):
    # What the trained model looks like: how good it is and what it learned.
    _model = get_ai_model()
    if _model is None:
        ai_model_panel = mo.md("_No model trained yet._")
    else:
        _names = []
        for _f in _model["features"]:
            _names.append(ai_model.FEATURE_LABELS[_f])
        _parts = [
            mo.md(
                f"**Model inputs:** {', '.join(_names)}  \n"
                f"**Trained on:** {_model['n_rows']} steps from {_model['n_tests']} tests"
            ),
        ]
        _error = _model["error"]
        if _error is None:
            _parts.append(mo.md("_Accuracy needs at least 2 tests._"))
        else:
            _parts.append(mo.md(
                "**Accuracy on a test the model has not seen** (average error, "
                "each test predicted by a model trained on the others):\n\n"
                "| | Model | Just guessing the average |\n|---|---|---|\n"
                f"| Static CoF | {_error['static_cof']['model']:.4f} | {_error['static_cof']['average_guess']:.4f} |\n"
                f"| Dynamic CoF | {_error['dynamic_cof']['model']:.4f} | {_error['dynamic_cof']['average_guess']:.4f} |\n\n"
                "The model is only useful when its error is clearly smaller than the guess."
            ))
        _parts.append(mo.md("**What the model learned** (change of the CoF per unit of each input):"))
        _parts.append(mo.ui.table(
            ai_model.coefficients_table(_model), selection=None,
            pagination=False, show_column_summaries=False, show_data_types=False,
        ))
        ai_model_panel = mo.vstack(_parts, gap=1)
    return (ai_model_panel,)


@app.cell
def _(ai_model, get_ai_model, mo):
    # The prediction inputs: the test conditions (every model input except
    # the speed), the speed program (the steps to predict, in U/min, in test
    # order) and the stroke (to turn U/min into m/s for the plots). Rebuilt
    # only when a new model is trained; created and laid out here for the
    # same reason as the data table above.
    _model = get_ai_model()
    ai_predict_inputs = None
    ai_predict_btn = mo.ui.run_button(label="&#128302; Predict")
    if _model is None:
        ai_predict_panel = mo.md("_Train a model first._")
    else:
        _boxes = {}
        for _name in _model["features"]:
            # speed and going up/down come from the speed program below,
            # the stroke from its own box (it is also needed for m/s).
            if _name == "speed" or _name == "going_down" or _name == "stroke_mm":
                continue
            if _name == "material":
                _boxes[_name] = mo.ui.dropdown(
                    options=_model["materials"], value=_model["materials"][0],
                    label=ai_model.FEATURE_LABELS[_name],
                )
            else:
                # Start in the middle of what the model was trained on.
                _low = _model["ranges"][_name][0]
                _high = _model["ranges"][_name][1]
                _boxes[_name] = mo.ui.number(
                    value=round((_low + _high) / 2, 2),
                    label=ai_model.FEATURE_LABELS[_name],
                )
        _stroke_default = 24
        if "stroke_mm" in _model["ranges"]:
            _stroke_default = _model["ranges"]["stroke_mm"][1]
        _boxes["stroke_mm"] = mo.ui.number(value=_stroke_default, start=0.1, label="Stroke [mm]")
        # Fixed-width wrapper: marimo's text box is sized to its host element.
        _program_tpl = mo.Html(
            '<div style="display:flex;align-items:center;gap:6px">'
            '<span style="font-size:0.82rem;color:#444;white-space:nowrap">Speed program [U/min]</span>'
            '<div style="width:440px">{speeds}</div></div>'
        )
        _boxes["speeds"] = _program_tpl.batch(speeds=mo.ui.text(
            value="30, 60, 120, 180, 240, 360, 480, 360, 240, 180, 120, 60, 30",
        ))
        ai_predict_inputs = mo.ui.dictionary(_boxes)

        _condition_boxes = []
        for _name in _boxes:
            if _name != "speeds":
                _condition_boxes.append(ai_predict_inputs[_name])
        ai_predict_panel = mo.vstack([
            mo.hstack(_condition_boxes, justify="start", align="end", gap=2, wrap=True),
            mo.hstack([ai_predict_inputs["speeds"], ai_predict_btn], justify="start", align="center", gap=2, wrap=True),
        ], gap=2)
    return ai_predict_btn, ai_predict_inputs, ai_predict_panel


@app.cell
def _(ai_model, ai_predict_btn, ai_predict_inputs, charts, get_ai_model, mo, set_ai_prediction):
    # "Predict": one prediction per step of the speed program, shown the same
    # way as a saved test on the Database tab - static and sliding friction against
    # mean velocity - plus the numbers as a table.
    if ai_predict_btn.value and ai_predict_inputs is not None:
        import pandas as _pd
        _model = get_ai_model()
        _values = ai_predict_inputs.value
        try:
            # The speed program: numbers separated by commas or spaces.
            _speeds = []
            for _part in _values["speeds"]["speeds"].replace(";", ",").replace(" ", ",").split(","):
                if _part.strip() == "":
                    continue
                _speed = ai_model.to_number(_part)
                if _speed is None or _speed <= 0:
                    raise ValueError(f"'{_part}' in the speed program is not a speed above 0")
                _speeds.append(_speed)
            if len(_speeds) == 0:
                raise ValueError("type at least one speed into the speed program")
            _stroke = _values["stroke_mm"]
            # 0 up to the fastest step of the program, 1 after it.
            _going_down = ai_model.going_down_flags(_speeds)

            _rows = []
            _outside = []
            for _k in range(len(_speeds)):
                _inputs = {}
                for _name in _model["features"]:
                    if _name == "speed":
                        _inputs[_name] = _speeds[_k]
                    elif _name == "going_down":
                        _inputs[_name] = _going_down[_k]
                    else:
                        _inputs[_name] = _values[_name]
                _predicted = ai_model.predict(_model, _inputs)
                for _name in ai_model.outside_training_range(_model, _inputs):
                    if _name not in _outside:
                        _outside.append(_name)
                _velocity = None
                if _stroke is not None and _stroke > 0:
                    _velocity = 2 * (_stroke / 1000.0) * _speeds[_k] / 60.0
                if _going_down[_k] == 1:
                    _direction = "down"
                else:
                    _direction = "up"
                _rows.append({
                    "Step": _k + 1,
                    "Speed [U/min]": _speeds[_k],
                    "Up / down": _direction,
                    "Mean velocity [m/s]": _velocity,
                    "Predicted static CoF": round(_predicted["static_cof"], 5),
                    "Static std dev": round(_predicted["static_sd"], 5),
                    "Predicted sliding CoF": round(_predicted["dynamic_cof"], 5),
                    "Sliding std dev": round(_predicted["dynamic_sd"], 5),
                })
            _table = _pd.DataFrame(_rows)

            # Same shape as database.get_step_results, so the saved test plot
            # function draws it, with the predicted std dev as error bars.
            _for_plot = _pd.DataFrame({
                "start": list(range(len(_speeds))),
                "end": list(range(1, len(_speeds) + 1)),
                "speed": _speeds,
                "static_mean": _table["Predicted static CoF"],
                "static_sd": _table["Static std dev"],
                "dynamic_mean": _table["Predicted sliding CoF"],
                "dynamic_sd": _table["Sliding std dev"],
            })
            _stroke_for_plot = None
            if _stroke is not None and _stroke > 0:
                _stroke_for_plot = float(_stroke)
            _figures = charts.build_friction_velocity_figures(_for_plot, _stroke_for_plot, "Prediction")

            _parts = []
            if len(_outside) > 0:
                _parts.append(mo.callout(mo.md(
                    "Careful: " + ", ".join(_outside)
                    + " goes outside the data the model learned from, so those values are a rough guess."
                ), kind="warn"))
            _parts.append(mo.ui.plotly(_figures[0]))
            _parts.append(mo.ui.plotly(_figures[1]))
            _parts.append(mo.ui.table(
                _table, selection=None,
                pagination=False, show_column_summaries=False, show_data_types=False,
            ))
            set_ai_prediction(mo.vstack(_parts, gap=1))
        except ValueError as _e:
            set_ai_prediction(mo.callout(mo.md(f"**Cannot predict:** {_e}"), kind="warn"))
    return


@app.cell
def _(PANEL_STYLE, ai_data_panel, ai_model_panel, ai_predict_panel, get_ai_msg, get_ai_prediction, mo):
    _msg = get_ai_msg()
    if _msg is None:
        _msg = mo.Html("")
    _prediction = get_ai_prediction()
    if _prediction is None:
        _prediction = mo.Html("")
    ai_tab = mo.vstack([
        mo.vstack([ai_data_panel, _msg], gap=2).style(PANEL_STYLE),
        mo.vstack([
            mo.Html('<p class="panel-title">3. Model</p>'),
            ai_model_panel,
        ], gap=1).style(PANEL_STYLE),
        mo.vstack([
            mo.Html('<p class="panel-title">4. Predict</p>'),
            ai_predict_panel,
            _prediction,
        ], gap=2).style(PANEL_STYLE),
    ], gap=2).style({"padding": "20px 0"})
    return (ai_tab,)


# ── Final layout ───────────────────────────────────────────────────────────
# Split into independent cells (rather than one monolithic layout cell) so
# that a widget somewhere getting rebuilt with a new identity - which
# happens legitimately whenever get_results_status_msg()'s content changes,
# i.e. after nearly every action in the app - only forces a re-render of
# the one small card that actually reads it, instead of resending the
# entire tab (chart included) and risking the frontend losing its
# connection to every other button in the process.
@app.cell
def _(calculate_btn, file_upload, get_results_status_msg, mo, open_excel_btn, PANEL_STYLE, parsed_file_id):
    if file_upload.value:
        _rvm_test = file_upload.value[0].name.replace(".txt", "")
    else:
        _rvm_test = "&mdash;"

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
        _status = mo.callout(mo.md("**New file uploaded** &mdash; click **Calculate** to parse it."), kind="warn")
    else:
        _status = get_results_status_msg()

    upload_card = mo.vstack([
        mo.hstack([file_upload, calculate_btn, open_excel_btn], justify="start", align="center"),
        _status,
        mo.Html('<hr class="divider">'),
        mo.Html(f'<div style="display:flex;flex-direction:column;gap:2px">'
                f'<span style="font-size:0.6rem;color:#999;font-weight:700;letter-spacing:1px">RVM TEST</span>'
                f'<span style="font-size:0.9rem;font-weight:600;color:#1f2a40">{_rvm_test}</span></div>'),
    ], gap=1).style(PANEL_STYLE)
    return (upload_card,)


@app.cell
def _(box_value_pusher, cof_chart, eval_table_panel, get_save_msg, mo, PANEL_STYLE, pulse_eval_field, results_panel, save_info_panel):
    # The chart iframe draws its own cards (pulse-offset strip, plot) so it
    # sits on the page directly, not inside a white card of its own; the
    # tables get their own card below it.
    _save_msg = get_save_msg()
    if _save_msg is None:
        _save_msg = mo.Html("")
    viz_card = mo.vstack([
        cof_chart,
        # invisible; only there so the chart's JS can find and write to it
        pulse_eval_field.style({"display": "none"}),
        box_value_pusher,
        mo.vstack([
            eval_table_panel,
            results_panel,
            save_info_panel,
            _save_msg,
        ], gap=1).style(PANEL_STYLE),
    ], gap=2)
    return (viz_card,)


@app.cell
def _(actions_row, mo, raw_data_card, upload_card, viz_card):
    results_tab = mo.vstack(
        [upload_card, raw_data_card, actions_row, viz_card], gap=2
    ).style({"padding": "20px 0"})
    return (results_tab,)


@app.cell
def _(db_selected_ids, mo):
    # "Export summary": the ticked tests side by side in one Excel sheet,
    # laid out like the lab's report sheet (see summary_export.py). The file
    # is only built when the button is clicked, and goes straight to the
    # browser's downloads - it is not stored anywhere.
    import datetime as _datetime
    import summary_export as _summary_export

    _ids = db_selected_ids

    def _build_file():
        return _summary_export.build_summary_excel(_ids)

    if len(_ids) == 0:
        summary_download = mo.download(
            data=b"", filename="summary.xlsx", disabled=True,
            label="&#128202; Export summary (select tests first)",
        )
    else:
        _stamp = _datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
        _count = f"{len(_ids)} tests"
        if len(_ids) == 1:
            _count = "1 test"
        summary_download = mo.download(
            data=_build_file,
            filename=f"Friction_summary_{_stamp}.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            label=f"&#128202; Export summary ({_count})",
        )
    return (summary_download,)


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

    help_button = mo.ui.button(label="&#10067; Help", on_click=_open_help)
    return (help_button,)


@app.cell
def _(mo):
    # Which of the two main sections is shown. mo.ui.tabs keys on the tab's
    # own label, so the state holds the label itself, and the labels live
    # here (rather than inline below) so the initial value can't drift out of
    # sync with the dict keys.
    # Emoji (and any other character outside Latin-1) are written as HTML
    # entities everywhere in this app, never as literal characters. marimo
    # sizes a cell's output with sys.getsizeof() on the Python string, and a
    # str holding even one such character is stored at 4 bytes per character
    # for the WHOLE string - the entire page is one output, so a single
    # literal emoji quadruples its measured size and trips marimo's 5 MB
    # output limit as soon as a chart is on the page.
    ANALYSIS_TAB = "&#128202;  Analysis"
    BATCH_TAB = "&#128193;  Batch"
    DATABASE_TAB = "&#128451;  Database"
    AI_TAB = "&#129504;  AI"
    get_active_tab, set_active_tab = mo.state(ANALYSIS_TAB)
    return AI_TAB, ANALYSIS_TAB, BATCH_TAB, DATABASE_TAB, get_active_tab, set_active_tab


@app.cell
def _(AI_TAB, ANALYSIS_TAB, BATCH_TAB, DATABASE_TAB, ai_tab, batch_tab, database_tab, get_active_tab, mo, results_tab):
    # Only the active tab's real content goes into the page. mo.ui.tabs puts
    # every tab's HTML into the one output marimo sizes against its 5 MB
    # limit, and each tab can hold a chart of ~2 MB - both at once was what
    # tipped it over. The hidden tab gets a light placeholder instead.
    # (mo.ui.tabs(lazy=True) would be the obvious tool, but marimo strips
    # <iframe> from lazily loaded HTML, and the charts are iframes.)
    #
    # This selection lives in its own cell, separate from the one that owns
    # the tabs' on_change: marimo never re-runs the cell that called a state
    # setter, and it attributes a setter called from on_change to the cell
    # that created the element. Reading get_active_tab() here instead makes
    # this cell re-run on every tab switch, and the tabs cell follows as its
    # dependent.
    _placeholder = mo.Html('<div style="min-height:200px"></div>')
    # Every tab starts as the placeholder; only the active one gets its content.
    tab_contents = {
        ANALYSIS_TAB: _placeholder,
        BATCH_TAB: _placeholder,
        DATABASE_TAB: _placeholder,
        AI_TAB: _placeholder,
    }
    if get_active_tab() == BATCH_TAB:
        tab_contents[BATCH_TAB] = batch_tab
    elif get_active_tab() == DATABASE_TAB:
        tab_contents[DATABASE_TAB] = database_tab
    elif get_active_tab() == AI_TAB:
        tab_contents[AI_TAB] = ai_tab
    else:
        tab_contents[ANALYSIS_TAB] = results_tab
    return (tab_contents,)


@app.cell
def _(get_active_tab, mo, set_active_tab, tab_contents):
    # value=/on_change= rather than a bare mo.ui.tabs(...): this cell depends
    # on tab_contents, which changes identity after nearly every action in
    # the app, so the tabs element is rebuilt often. Without the remembered
    # value, each of those rebuilds would silently drop the view back to the
    # first tab mid-work.
    main_tabs = mo.ui.tabs(
        tab_contents,
        value=get_active_tab(),
        on_change=set_active_tab,
    )
    return (main_tabs,)


@app.cell
def _(help_button, main_tabs, mo):
    _navbar = mo.Html(f"""
    <div class="navbar">
      <div><span class="navbar-title">FRICTION EVALUATION</span><span class="navbar-version">v2.0</span></div>
      <div class="navbar-right">
        {help_button}
      </div>
    </div>
    """)

    mo.vstack([
        _navbar,
        main_tabs,
    ], gap=0).style({"max-width": "1280px", "margin": "0 auto"})
    return


if __name__ == "__main__":
    app.run()
