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


def _cells(line):
    """The tab-separated cells of one line, without spaces around them."""
    cells = []
    for cell in line.split("\t"):
        cells.append(cell.strip())
    return cells


def _column_of(cells, wanted):
    """The column number (1 = first) of the cell that is exactly `wanted`
    (not minding upper/lower case), or None."""
    for k in range(len(cells)):
        if cells[k].lower() == wanted.lower():
            return k + 1
    return None


def _column_starting_with(cells, start):
    """The column number (1 = first) of the first cell starting with
    `start` (not minding upper/lower case), or None."""
    for k in range(len(cells)):
        if cells[k].lower().startswith(start.lower()):
            return k + 1
    return None


def _number(text):
    """The cell as a number (decimal comma), or None."""
    try:
        return float(text.replace(",", "."))
    except ValueError:
        return None


def detect_raw_data_settings(raw_text: str):
    """Find the Raw Data settings (rows and columns) from the words in an
    OFT file, for "Automatic" on the Raw Data card. Returns (settings,
    problems): settings has the same keys as the Raw Data boxes (as text,
    rows and columns counted from 1) plus "has_step"; problems lists what
    could not be found (then the settings can't be used).

    What it looks for:
    - Main data: the line naming the columns ("Nummer", "Zeit", ...). The
      data starts at the first line after it that begins with a number (the
      line in between holds the units). Columns: "Zeit", "RK OFT Links",
      "RK OFT Rechts" and "Belastung".
    - Step data: "Versuch mit Stufen" Ja/Nein, the line with
      "Startzeit [s]" and "Drehzahl [U/min]", and the "Stufe ..." lines
      below it. The steps start at the slowest speed before the fastest one,
      so the warm-up steps at the start (e.g. 120 U/min at 10 N, then at the
      test load) are left out; steps of no length (two steps starting at
      the same time) are left out too. They end at the last "Stufe" line.
    """
    lines = raw_text.splitlines()
    settings = {"stop_main_row": "0"}
    problems = []

    # ── Main data ────────────────────────────────────────────────────────────
    header_index = None
    for i in range(len(lines)):
        cells = _cells(lines[i])
        if _column_of(cells, "Zeit") is not None and _column_of(cells, "Belastung") is not None:
            header_index = i
            break
    if header_index is None:
        problems.append("no line naming the columns (with 'Zeit' and 'Belastung')")
    else:
        cells = _cells(lines[header_index])
        for key, wanted in [("col_time", "Zeit"), ("col_left", "RK OFT Links"),
                            ("col_right", "RK OFT Rechts"), ("col_load", "Belastung")]:
            column = _column_of(cells, wanted)
            if column is None:
                problems.append(f"no column '{wanted}'")
            else:
                settings[key] = str(column)
        for i in range(header_index + 1, min(header_index + 6, len(lines))):
            first = _cells(lines[i])[0]
            if first != "" and _number(first) is not None:
                settings["start_main_row"] = str(i + 1)
                break
        if "start_main_row" not in settings:
            problems.append("no numbers below the line naming the columns")

    # ── Step data ────────────────────────────────────────────────────────────
    has_step = None
    for line in lines[:200]:
        cells = _cells(line)
        if len(cells) >= 2 and cells[0].lower() == "versuch mit stufen":
            has_step = cells[1].lower() == "ja"
            break
    step_header = None
    for i in range(min(len(lines), 300)):
        cells = _cells(lines[i])
        if _column_starting_with(cells, "Startzeit") is not None:
            step_header = i
            break
    if has_step is None:
        has_step = step_header is not None
    settings["has_step"] = has_step
    if not has_step:
        settings["start_step_row"] = "0"
        settings["end_step_row"] = "0"
        settings["step_col_time"] = "1"
        settings["step_col_speed"] = "0"
        return settings, problems
    if step_header is None:
        problems.append("the file has steps, but no line with 'Startzeit'")
        return settings, problems

    cells = _cells(lines[step_header])
    time_column = _column_starting_with(cells, "Startzeit")
    speed_column = _column_starting_with(cells, "Drehzahl")
    settings["step_col_time"] = str(time_column)
    if speed_column is None:
        problems.append("no step column 'Drehzahl'")
        return settings, problems
    settings["step_col_speed"] = str(speed_column)

    # The "Stufe" lines: (line number, start time, speed)
    steps = []
    for i in range(step_header + 1, len(lines)):
        cells = _cells(lines[i])
        if not cells[0].lower().startswith("stufe"):
            break
        start = None
        speed = None
        if len(cells) >= time_column:
            start = _number(cells[time_column - 1])
        if len(cells) >= speed_column:
            speed = _number(cells[speed_column - 1])
        if start is None or speed is None:
            problems.append(f"line {i + 1} is a step without a start time or speed")
            return settings, problems
        steps.append((i + 1, start, speed))
    if len(steps) == 0:
        problems.append("no 'Stufe' lines below 'Startzeit'")
        return settings, problems

    # Steps of no length at the start: the next one starts at the same time
    first = 0
    while first < len(steps) - 1 and steps[first + 1][1] <= steps[first][1]:
        first = first + 1
    # The fastest step, then the slowest one up to it
    fastest = first
    for k in range(first, len(steps)):
        if steps[k][2] > steps[fastest][2]:
            fastest = k
    slowest = first
    for k in range(first, fastest + 1):
        if steps[k][2] < steps[slowest][2]:
            slowest = k
    settings["start_step_row"] = str(steps[slowest][0])
    settings["end_step_row"] = str(steps[-1][0])
    return settings, problems


def describe_detected_settings(settings):
    """One line for the user: what "Automatic" read from the file."""
    text = (f"main data from row {settings['start_main_row']}: Zeit col {settings['col_time']}, "
            f"friction L/R col {settings['col_left']}/{settings['col_right']}, "
            f"Belastung col {settings['col_load']}")
    if settings["has_step"]:
        text = (f"steps rows {settings['start_step_row']}-{settings['end_step_row']} "
                f"(Startzeit col {settings['step_col_time']}, Drehzahl col {settings['step_col_speed']}); "
                + text)
    else:
        text = "no step data; " + text
    return text


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
