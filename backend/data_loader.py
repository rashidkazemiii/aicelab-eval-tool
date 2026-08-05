import io

import pandas as pd


def parse_main_and_step_data(raw_text: str, params: dict):
    """Parse the main data block and (optionally) the step block from a raw
    .txt upload, per the row/column indices in `params` (raw_data_form.value).

    Returns (df_raw, step_df); step_df is None if step data isn't present or
    not enabled via params["has_step"]. Raises on malformed input (int()
    conversion errors, pandas parsing errors) — the caller is expected to
    wrap this in its own try/except, same as when this logic was inline.
    """
    _lines = raw_text.splitlines()

    _start_main = int(params["start_main_row"])
    _stop_main  = int(params["stop_main_row"])
    _start_step = int(params["start_step_row"])
    _end_step   = int(params["end_step_row"])
    _col_time   = int(params["col_time"])

    # ── Main data ────────────────────────────────────────────────────────────
    _nrows = (_stop_main - _start_main + 1 if _stop_main > _start_main else None)
    df_raw = pd.read_csv(
        io.StringIO(raw_text), sep="\t",
        # start_main_row is the 1-indexed spreadsheet row of the header;
        # -2 converts it to a 0-indexed skiprows count (row 1 -> skiprows 0).
        skiprows=_start_main - 2,
        nrows=_nrows,
        decimal=",", low_memory=False,
    )
    df_raw.columns = df_raw.columns.str.strip()
    df_raw = df_raw.apply(pd.to_numeric, errors="coerce")

    # ── Step data (optional) ────────────────────────────────────────────────
    step_df = None
    if bool(params["has_step"]) and _start_step > 0 and _end_step > _start_step:
        # Same 1-indexed-row -> 0-indexed-list-slice conversion as above.
        _step_text = "\n".join(_lines[_start_step - 2 : _end_step])
        step_df = pd.read_csv(io.StringIO(_step_text), sep="\t", decimal=",")
        step_df.columns = step_df.columns.str.strip()
        for _c in step_df.columns[1:]:
            step_df[_c] = pd.to_numeric(step_df[_c], errors="coerce")
        _t_col    = step_df.columns[1]
        _zeit_col = df_raw.columns[_col_time - 1] if _col_time > 0 else df_raw.columns[1]
        step_df["Endzeit [s]"] = step_df[_t_col].shift(-1)
        step_df.loc[step_df.index[-1], "Endzeit [s]"] = df_raw[_zeit_col].max()
        if _t_col != "Startzeit [s]":
            step_df = step_df.rename(columns={_t_col: "Startzeit [s]"})
        step_df["inactive"] = False

    return df_raw, step_df


def parse_preview_table(raw_text: str) -> pd.DataFrame:
    """Build the full-file line-by-line preview table shown in the Raw Data
    tab: every line of the upload (including headers/step rows), split on
    tab, unfiltered, with a leading 1-indexed "#" row-number column.

    NOT the same computation as parse_main_and_step_data, despite the
    superficial similarity of reading the same raw text — this shows the
    entire raw file for user reference, while parse_main_and_step_data slices
    out just the numeric main-data block used for calculation. Do not merge
    the two; that would risk a real behavior change in either code path.
    """
    _lines = raw_text.splitlines()
    _rows = [line.split("\t") for line in _lines]
    _ncols = max(len(r) for r in _rows)
    _rows_padded = [r + [""] * (_ncols - len(r)) for r in _rows]
    df_file = pd.DataFrame(_rows_padded, columns=[str(i) for i in range(_ncols)])
    df_file.insert(0, "#", range(1, len(_lines) + 1))
    return df_file
