"""Batch evaluation: run many uploaded .txt files through the same steps
a user would click through on the Analysis tab, and save each result.

For one file the steps are:
  read (Raw Data settings) -> CoF -> Offset ON -> Filter -> Find zeros
  -> speed pulse (pulse offset 0 ms) -> Evaluate with pulse -> statistics
  -> Save.

The settings (Raw Data rows/columns, Filter pts, Static %, Dyn min/max %)
are taken once, when the batch is started, and used for every file.

The files are uploaded through the browser (not read from a folder on
disk), so this works the same when the app runs as a server and the files
are on the user's own computer.
"""

import contextlib
import io

import data_loader
import database
import pipeline
import speed_pulse


def make_plan(uploaded_files, raw_params, filter_params, eval_params):
    """Everything a batch run needs, captured at the moment Run is clicked:
    the uploaded .txt files (name -> file contents), which of them are
    already saved in the database (by file name), and the settings to use.

    `uploaded_files` is the upload widget's .value - a list of uploads,
    each with a .name and its .contents (bytes)."""
    contents = {}
    for upload in uploaded_files:
        if upload.name.lower().endswith(".txt"):
            contents[upload.name] = upload.contents
    files = sorted(contents.keys())
    existing = []
    for name in files:
        if database.find_existing_test(name) is not None:
            existing.append(name)
    return {
        "files": files,
        "contents": contents,
        "existing": existing,
        "raw_params": raw_params,
        "filter_params": filter_params,
        "eval_params": eval_params,
    }


def evaluate_file(raw_text, raw_params, filter_params, eval_params):
    """Run one file (its text) through the whole pipeline. Returns a dict
    with the pieces database.save_full_evaluation needs. Raises on any
    error."""

    # parse_main_and_step_data prints the step lines it reads - useful for
    # one file, just noise for a whole folder.
    with contextlib.redirect_stdout(io.StringIO()):
        df_raw, step_df = data_loader.parse_main_and_step_data(raw_text, raw_params)
    if step_df is None or "Drehzahl" not in step_df.columns:
        raise Exception("no step data with Drehzahl - Evaluate with pulse needs it")

    df_display = pipeline.compute_display_df(df_raw, step_df, raw_params, True)
    df_proc = pipeline.compute_filtered_df(df_display, filter_params)
    zero_crossings = pipeline.compute_zero_crossings(df_proc)

    pulse = speed_pulse.build_speed_pulse(df_display, step_df, zero_crossings)
    if pulse is None:
        raise Exception("could not build the speed pulse")

    cof_eval = pipeline.compute_pulse_evaluation(df_display, pulse["edges"], eval_params)
    if cof_eval is None:
        raise Exception("Evaluate with pulse found no cycles")
    stats_result = pipeline.compute_stats(cof_eval, df_display, step_df)

    return {
        "df_display": df_display,
        "df_proc": df_proc,
        "filter_active": pipeline.is_filter_active(filter_params, df_proc),
        "cof_eval": cof_eval,
        "stats_result": stats_result,
        "step_df": step_df,
        "stroke_mm": data_loader.read_stroke_mm(raw_text),
    }


def skipped_step_names(result):
    """'102-105 s, 105-108 s' for the steps Evaluate with pulse left out."""
    names = []
    step_df = result["step_df"]
    for step_index in result["cof_eval"]["skipped_steps"]:
        row = step_df.iloc[step_index]
        names.append(f"{round(row['Startzeit [s]'])}-{round(row['Endzeit [s]'])} s")
    return ", ".join(names)


def run_one(plan, name, overwrite):
    """Evaluate and save one file of the plan. Returns one row for the
    batch log: file, status, cycles, skipped steps, test id."""
    row = {"File": name, "Status": "", "Cycles": None, "Skipped steps": "", "Test id": None}

    existing = database.find_existing_test(name)
    if existing is not None and not overwrite:
        row["Status"] = "Skipped: already saved"
        return row

    try:
        raw_text = plan["contents"][name].decode("latin-1")
        result = evaluate_file(
            raw_text,
            plan["raw_params"], plan["filter_params"], plan["eval_params"],
        )
        # The hand-typed conditions of the old copy move to the new one.
        old_details = None
        if existing is not None:
            old_details = database.get_test_details(existing.id)
            database.delete_test(existing.id)
        test_id = database.save_full_evaluation(
            name, plan["filter_params"], plan["eval_params"],
            result["df_display"], result["df_proc"], result["filter_active"],
            result["cof_eval"], result["stats_result"],
            step_df=result["step_df"],
        )
        details = old_details
        if details is None:
            details = database.get_test_details(test_id)
        # The stroke comes from the file, so the file's value wins.
        if result["stroke_mm"] is not None:
            details["stroke_mm"] = result["stroke_mm"]
        database.save_test_details(test_id, details)
        if existing is not None:
            row["Status"] = "Overwritten"
        else:
            row["Status"] = "Saved"
        row["Cycles"] = len(result["cof_eval"]["cof_res"])
        row["Skipped steps"] = skipped_step_names(result)
        row["Test id"] = test_id
    except Exception as e:
        row["Status"] = f"Error: {e}"
    return row
