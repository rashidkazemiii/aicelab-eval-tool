import io
import os
import tempfile
import time

import pandas as pd


def is_ready_to_parse(file_present: bool, params: dict | None) -> bool:
    """True once there's an uploaded file and a real start_main_row, so
    Calculate has enough to try parsing.
    """
    if not file_present:
        return False
    if params is None:
        return False
    return int(params["start_main_row"]) > 0


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
    _step_col_time = int(params["step_col_time"])

    # ── Main data ────────────────────────────────────────────────────────────
    if _stop_main > _start_main:
        _nrows = _stop_main - _start_main + 1
    else:
        _nrows = None
    df_raw = pd.read_csv(
        io.StringIO(raw_text), sep="\t",
        # start_main_row is the 1-indexed line where the real data starts -
        # there is no header row to look for, so pandas must not treat the
        # first line as column names (header=None). Which column is which
        # (Zeit, RK OFT Links, ...) is decided purely by the column numbers
        # the user gives (col_time, col_left, ...), never by guessing from
        # the raw text.
        skiprows=_start_main - 1,
        nrows=_nrows,
        decimal=",", low_memory=False,
        header=None,
    )
    df_raw = df_raw.apply(pd.to_numeric, errors="coerce")

    # ── Step data (optional) ────────────────────────────────────────────────
    step_df = None
    _has_step = bool(params["has_step"])
    _step_rows_given = _start_step > 0 and _end_step > _start_step
    if _has_step and _step_rows_given:
        # 1-indexed line number -> 0-indexed list position: line N is at
        # position N-1, so the header line itself starts the slice here.
        _step_lines = _lines[_start_step - 1 : _end_step]
        print("Step lines being read:")
        for _line in _step_lines:
            print(_line)
        _step_text = "\n".join(_step_lines)
        # These lines are pure data, chosen by the user - there is no header
        # row to look for, so pandas must not treat the first line as column
        # names (header=None). Which column holds Startzeit is decided by
        # step_col_time (given by the user), never guessed from the raw text.
        step_df = pd.read_csv(io.StringIO(_step_text), sep="\t", decimal=",", header=None)
        for _c in step_df.columns[1:]:
            step_df[_c] = pd.to_numeric(step_df[_c], errors="coerce")
        _t_col = step_df.columns[_step_col_time - 1]
        if _col_time > 0:
            _zeit_col = df_raw.columns[_col_time - 1]
        else:
            _zeit_col = df_raw.columns[1]
        step_df["Endzeit [s]"] = step_df[_t_col].shift(-1)
        step_df.loc[step_df.index[-1], "Endzeit [s]"] = df_raw[_zeit_col].max()
        step_df = step_df.rename(columns={_t_col: "Startzeit [s]"})
        step_df["inactive"] = False
        print("Endzeit [s] computed for each step:")
        for _value in step_df["Endzeit [s]"]:
            print(_value)

    return df_raw, step_df


def _unique_temp_csv_path(base_name: str) -> str:
    # A unique name per call, not a fixed one: once Excel has opened a file,
    # Windows keeps it locked for as long as Excel has it open, so writing
    # the same path again on a second click fails with PermissionError.
    unique_suffix = str(int(time.time() * 1000))
    return os.path.join(tempfile.gettempdir(), f"{base_name}_{unique_suffix}.csv")


def open_in_excel(raw_text: str, file_name: str) -> str:
    """Write the raw upload out as a semicolon-separated .csv and open it in
    Excel. Semicolon, not comma, because the data itself uses a comma as its
    decimal point (German locale) - a comma-separated .csv would split every
    number's decimal point into its own column. Semicolon is also the
    default CSV list separator on a comma-decimal Windows system, so Excel
    opens the file with columns already split, no import wizard needed.

    Returns the temp file path that was written and opened.
    """
    csv_lines = []
    for line in raw_text.splitlines():
        csv_lines.append(line.replace("\t", ";"))
    csv_text = "\n".join(csv_lines)

    if file_name:
        base_name = os.path.splitext(file_name)[0]
    else:
        base_name = "raw_data"
    path = _unique_temp_csv_path(base_name)
    with open(path, "w", encoding="latin-1") as f:
        f.write(csv_text)

    os.startfile(path)
    return path


def open_dataframe_in_excel(df: pd.DataFrame, base_name: str) -> str:
    """Write a DataFrame out as a semicolon-separated .csv (same reasoning
    as open_in_excel - the numbers themselves use '.' as their decimal
    point, but the surrounding raw files are German-locale, so semicolon
    keeps this consistent with the rest of the app's Excel exports) and open
    it in Excel. Returns the temp file path that was written and opened.

    Meant for a table that's too large to send to the browser and show
    inline (mo.ui.table) without tripping marimo's output-size limit - the
    combined per-sample + per-cycle results table, say - where Excel is the
    only practical way left to look at it as one table.
    """
    path = _unique_temp_csv_path(base_name)
    df.to_csv(path, index=False, sep=";")
    os.startfile(path)
    return path
