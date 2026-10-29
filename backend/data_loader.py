import io

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
        _step_col_speed = int(params.get("step_col_speed", 0))
        if _step_col_speed > 0:
            _speed_col = step_df.columns[_step_col_speed - 1]
            step_df = step_df.rename(columns={_speed_col: "Drehzahl"})
        step_df["inactive"] = False
        print("Endzeit [s] computed for each step:")
        for _value in step_df["Endzeit [s]"]:
            print(_value)

    return df_raw, step_df


def read_stroke_mm(raw_text: str):
    """The stroke [mm] from the file header line "Hub Exzenter<TAB>24,0<TAB>mm",
    or None when the file has no such line (or its value is not a number)."""
    for line in raw_text.splitlines():
        parts = line.split("\t")
        if parts[0].strip() == "Hub Exzenter" and len(parts) >= 2:
            try:
                return float(parts[1].strip().replace(",", "."))
            except ValueError:
                return None
    return None


def raw_text_to_csv_bytes(raw_text: str) -> bytes:
    """The raw upload as a semicolon-separated .csv file (as bytes), for
    the browser to download and open in Excel. Semicolon, not comma,
    because the data itself uses a comma as its decimal point (German
    locale) - a comma-separated .csv would split every number's decimal
    point into its own column. Semicolon is also the default CSV list
    separator on a comma-decimal Windows system, so Excel opens the file
    with columns already split, no import wizard needed.

    A download, not "open Excel here": when the app runs as a server, the
    file has to end up on the user's own computer, not on the server.
    """
    csv_lines = []
    for line in raw_text.splitlines():
        csv_lines.append(line.replace("\t", ";"))
    csv_text = "\n".join(csv_lines)
    return csv_text.encode("latin-1")


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """A DataFrame as a semicolon-separated .csv file (as bytes), for the
    browser to download and open in Excel (semicolon for the same reason
    as raw_text_to_csv_bytes - it keeps this consistent with the rest of
    the app's Excel exports).

    Meant for a table that's too large to send to the browser and show
    inline (mo.ui.table) without tripping marimo's output-size limit - the
    combined per-sample + per-cycle results table, say - where Excel is the
    only practical way left to look at it as one table.
    """
    csv_text = df.to_csv(index=False, sep=";")
    # utf-8-sig (with a BOM) so Excel reads special characters (°, µ) right
    return csv_text.encode("utf-8-sig")
