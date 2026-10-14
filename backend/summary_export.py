"""The "Export summary" Excel file for the History tab: the saved tests the
user selected, side by side, laid out like the lab's report sheet
(RTU_Ice-Friction-2026_1.xlsx, rows 1-53):

    STATIC FRICTION                       (one block of 5 columns per test)
      Test / Sample / Normal force / Ice / Relative humidity / Temperature
      Ice bath / Ice surface temperature / Ice unevenness (mean / std dev)
      v (m/s) | Average | St. Dev. | n | Ss | Ss2
      one row per step: running-in, then the speed going up to "max.",
      then coming back down (column B = the real velocity, column C = the
      position on the mirrored axis, like the report charts)
    SLIDING FRICTION                      (same layout, dynamic CoF)

Ss is the sum of the values (Average x n) and Ss2 the sum of their squares
- the same numbers the app already stores per step. Anything the app does
not know (normal force, dry/wet ice, ice temperatures, unevenness) is left
empty.

The look (colours, borders, fonts, number formats, column widths, row
heights) comes from templates/summary_template.xlsx: rows 1-53 of the
report sheet with all data removed and one test block (columns D-H). That
block's formatting is repeated for every further test, and column I - the
light background right of the last block - moves along to the right.

Only builds the file in memory (bytes); nothing is saved anywhere.
"""

import copy
import io
import os

import openpyxl

import database

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "templates", "summary_template.xlsx")
TEMPLATE_LAST_ROW = 53
TEMPLATE_BACKGROUND_COLUMN = 9   # column I: the area right of the test block

LABEL_COLUMN = 3          # column C
FIRST_TEST_COLUMN = 4     # column D
COLUMNS_PER_TEST = 5      # Average, St. Dev., n, Ss, Ss2
STATIC_SECTION_ROW = 3    # "STATIC FRICTION"
STEP_MATCH_TOLERANCE_S = 0.05

PHASE_ORDER = {"running-in": 0, "up": 1, "down": 2}


def _phases(speeds):
    """For a test's step speeds in time order: "running-in" for the steps
    before the first slowest step, "down" for the steps after the first
    fastest step, "up" for the rest."""
    slowest = 0
    fastest = 0
    for k in range(len(speeds)):
        if speeds[k] < speeds[slowest]:
            slowest = k
        if speeds[k] > speeds[fastest]:
            fastest = k
    phases = []
    for k in range(len(speeds)):
        if k < slowest and slowest < fastest:
            phases.append("running-in")
        elif k > fastest:
            phases.append("down")
        else:
            phases.append("up")
    return phases


def _load_test(test_id):
    """A saved test's header values and its steps: a list of
    {"key": (phase, speed, occurrence), "result": Result or None}."""
    db = database.SessionLocal()
    try:
        test = db.query(database.Test).filter(database.Test.id == test_id).first()
        if test is None:
            return None
        steps = (
            db.query(database.Step).filter(database.Step.test_id == test_id)
            .order_by(database.Step.step_index).all()
        )
        results = db.query(database.Result).filter(database.Result.test_id == test_id).all()
    finally:
        db.close()

    with_speed = []
    for s in steps:
        if s.speed is not None and not s.inactive:
            with_speed.append(s)
    speeds = []
    for s in with_speed:
        speeds.append(float(s.speed))
    phases = _phases(speeds)

    step_rows = []
    seen = {}
    for k in range(len(with_speed)):
        step = with_speed[k]
        # The same phase and speed can come twice (e.g. two running-in
        # steps); the occurrence number keeps them apart.
        base_key = (phases[k], speeds[k])
        occurrence = seen.get(base_key, 0)
        seen[base_key] = occurrence + 1
        match = None
        for r in results:
            parts = str(r.time_range or "").replace("–", "-").split("-")
            if len(parts) != 2:
                continue
            try:
                start = float(parts[0])
                end = float(parts[1])
            except ValueError:
                continue
            if abs(start - step.start_time) <= STEP_MATCH_TOLERANCE_S and abs(end - step.end_time) <= STEP_MATCH_TOLERANCE_S:
                match = r
                break
        step_rows.append({"key": (phases[k], speeds[k], occurrence), "result": match})

    name = test.file_name
    if name.lower().endswith(".txt"):
        name = name[:-4]
    return {
        "name": name,
        "material": test.material,
        "humidity": test.humidity,
        "temperature": test.temperature,
        "stroke_mm": test.stroke_mm,
        "steps": step_rows,
    }


def _sort_key(key):
    """Rows in report order: running-in (as they came), then going up
    (slow to fast), then coming down (fast to slow)."""
    phase, speed, occurrence = key
    if phase == "down":
        return (PHASE_ORDER[phase], -speed, occurrence)
    if phase == "running-in":
        return (PHASE_ORDER[phase], occurrence, speed)
    return (PHASE_ORDER[phase], speed, occurrence)


def _velocity(speed, stroke_mm):
    """Mean sliding velocity [m/s] = 2 * stroke * Drehzahl / 60."""
    return 2 * (stroke_mm / 1000.0) * speed / 60.0


def build_summary_excel(test_ids):
    """The .xlsx file (as bytes) for the given saved tests."""
    tests = []
    for test_id in test_ids:
        test = _load_test(test_id)
        if test is not None:
            tests.append(test)
    tests.sort(key=_test_name)

    # One row per step, from every selected test together.
    keys = []
    for test in tests:
        for step in test["steps"]:
            if step["key"] not in keys:
                keys.append(step["key"])
    keys.sort(key=_sort_key)
    # The report always has a running-in row at the top; when no selected
    # test has a running-in step it stays empty (speed None).
    has_running_in = False
    for key in keys:
        if key[0] == "running-in":
            has_running_in = True
    if not has_running_in:
        keys.insert(0, ("running-in", None, 0))

    # The velocity column uses the stroke of the first test that has one.
    stroke = None
    for test in tests:
        if test["stroke_mm"] is not None:
            stroke = test["stroke_mm"]
            break
    fastest_speed = 0.0
    for key in keys:
        if key[1] is not None and key[1] > fastest_speed:
            fastest_speed = key[1]

    workbook = openpyxl.load_workbook(TEMPLATE_PATH)
    sheet = workbook.active
    _format_test_blocks(sheet, len(tests))

    sheet.cell(2, LABEL_COLUMN, "Separate display for increasing and decreasing velocity")
    static_end = _write_section(sheet, STATIC_SECTION_ROW, "STATIC FRICTION", "static",
                                tests, keys, stroke, fastest_speed)
    _write_section(sheet, static_end + 2, "SLIDING FRICTION", "dynamic",
                   tests, keys, stroke, fastest_speed)

    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def _test_name(test):
    return test["name"]


def _format_test_blocks(sheet, n_tests):
    """Give every test after the first the template's formatting of the
    first block (columns D-H), and put the background column right of the
    last block."""
    # Remember the background column's look before a block overwrites it.
    background = []
    for r in range(1, TEMPLATE_LAST_ROW + 1):
        background.append(copy.copy(sheet.cell(r, TEMPLATE_BACKGROUND_COLUMN)._style))
    for t in range(1, n_tests):
        for k in range(COLUMNS_PER_TEST):
            for r in range(1, TEMPLATE_LAST_ROW + 1):
                source = sheet.cell(r, FIRST_TEST_COLUMN + k)
                target = sheet.cell(r, FIRST_TEST_COLUMN + t * COLUMNS_PER_TEST + k)
                target._style = copy.copy(source._style)
    after_last = FIRST_TEST_COLUMN + max(n_tests, 1) * COLUMNS_PER_TEST
    for r in range(1, TEMPLATE_LAST_ROW + 1):
        sheet.cell(r, after_last)._style = copy.copy(background[r - 1])


def _write_section(sheet, start_row, title, kind, tests, keys, stroke, fastest_speed):
    """One section (static or sliding friction). Returns its last row.
    Only writes values - the look comes from the template."""
    sheet.cell(start_row, LABEL_COLUMN, title)

    labels = [
        "Test",
        "Sample",
        "Normal force",
        "Ice",
        "Relative humidity (%)",
        "Temperature (°C)",
        "Ice bath temperature in °C (mean / standard deviation)",
        "Ice surface temperature in °C (mean / standard deviation)",
        "Ice unevenness in µm (max-min difference / standard deviation)",
    ]
    for k in range(len(labels)):
        sheet.cell(start_row + 1 + k, LABEL_COLUMN, labels[k])

    header_row = start_row + 1 + len(labels)
    sheet.cell(header_row, LABEL_COLUMN, "v (m/s)")

    for t in range(len(tests)):
        test = tests[t]
        column = FIRST_TEST_COLUMN + t * COLUMNS_PER_TEST
        sheet.cell(start_row + 1, column, test["name"])
        sheet.cell(start_row + 2, column, test["material"])
        # Normal force and Ice (dry / wet) are not known: left empty.
        sheet.cell(start_row + 5, column, test["humidity"])
        sheet.cell(start_row + 6, column, test["temperature"])
        # Ice bath / surface temperature and unevenness: not known, empty.
        headers = ["Average", "St. Dev.", "n", "Ss", "Ss2"]
        for h in range(len(headers)):
            sheet.cell(header_row, column + h, headers[h])

    row = header_row + 1
    running_in_labelled = False
    for key in keys:
        phase, speed, occurrence = key
        if speed is None:
            # the empty running-in row
            sheet.cell(row, 2, "running-in")
            running_in_labelled = True
            row = row + 1
            continue
        if stroke is not None:
            velocity = _velocity(speed, stroke)
            fastest_velocity = _velocity(fastest_speed, stroke)
        else:
            velocity = None
            fastest_velocity = None

        # Columns B and C, as in the report sheet.
        if phase == "running-in":
            if not running_in_labelled:
                sheet.cell(row, 2, "running-in")
                running_in_labelled = True
            position = velocity
        elif phase == "up":
            if speed == fastest_speed:
                sheet.cell(row, 2, "max.")
            position = velocity
        else:
            if velocity is not None:
                sheet.cell(row, 2, velocity)
                position = 2 * fastest_velocity - velocity
            else:
                position = None
        if position is not None:
            sheet.cell(row, LABEL_COLUMN, round(position, 6))
        else:
            # No stroke known for any selected test: show the speed instead.
            sheet.cell(row, LABEL_COLUMN, f"{speed:g} U/min")

        for t in range(len(tests)):
            result = None
            for step in tests[t]["steps"]:
                if step["key"] == key:
                    result = step["result"]
            if result is None:
                continue
            if kind == "static":
                values = [result.static_mean_cof, result.static_sd, result.static_n,
                          result.static_sum, result.static_variance]
            else:
                values = [result.dynamic_mean_cof, result.dynamic_sd, result.dynamic_n,
                          result.dynamic_sum, result.dynamic_variance]
            if values[0] is None:
                continue  # step skipped (noisy / no cycles): leave it empty
            column = FIRST_TEST_COLUMN + t * COLUMNS_PER_TEST
            for v in range(len(values)):
                sheet.cell(row, column + v, values[v])
        row = row + 1
    return row - 1
