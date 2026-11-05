"""The information typed in about a test: reading what the user typed on the
save form, the History form and the Database tab's table.

Everything is typed as text. A "number" column must hold a number (a decimal
comma is fine); an empty box means "not known".
"""

import html

import pandas as pd

import ai_model
import database


def value_as_text(value):
    """A stored value as the text shown in a box. "" when it is empty."""
    if value is None:
        return ""
    return str(value)


def html_label(name):
    """A column name, safe to put into the page: HTML-escaped, curly braces
    written out (a form template would read them as a placeholder), and only
    plain characters - see ANALYSIS_TAB in app.py for why."""
    text = html.escape(name)
    text = text.replace("{", "&#123;").replace("}", "&#125;")
    return text.encode("ascii", "xmlcharrefreplace").decode("ascii")


def _is_empty(typed):
    if typed is None:
        return True
    if isinstance(typed, float) and pd.isna(typed):
        return True
    text = str(typed).strip()
    return text == "" or text.lower() in ("nan", "none")


def read_typed_value(column, typed):
    """One typed value of a column. Returns (value, is_valid): value is
    None for an empty box; is_valid is False when a number column holds
    something that is not a number."""
    if _is_empty(typed):
        return None, True
    if column["kind"] == "number":
        number = ai_model.to_number(typed)
        if number is None:
            return None, False
        return number, True
    return str(typed).strip(), True


def read_typed_values(columns, typed):
    """Read a filled-in form. `typed` is {column key: typed text}. Returns
    {"values": {column id: value}, "empty": [column names],
    "not_numbers": [column names]}."""
    values = {}
    empty = []
    not_numbers = []
    for column in columns:
        value, is_valid = read_typed_value(column, typed.get(column["key"]))
        if not is_valid:
            not_numbers.append(column["name"])
        elif value is None:
            empty.append(column["name"])
        values[column["id"]] = value
    return {"values": values, "empty": empty, "not_numbers": not_numbers}


def _text_or_empty(value):
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value)


def build_database_table():
    """The Database tab's table: one row per saved test, newest first. All
    cells are text, so that an empty cell is simply "". Only the columns from
    list_info_columns can be edited; the rest shows how the test was
    evaluated."""
    columns = database.list_info_columns()
    all_values = database.get_all_info_values()
    rows = []
    for test in database.list_tests():
        row = {"id": test["id"], "File name": test["file_name"]}
        n_empty = 0
        values = all_values.get(test["id"], {})
        for column in columns:
            text = value_as_text(values.get(column["id"]))
            row[column["name"]] = text
            if text == "":
                n_empty = n_empty + 1
        row["Empty fields"] = n_empty
        row["Saved"] = _text_or_empty(test["uploaded_at"])[:16]
        row["Filter pts"] = _text_or_empty(test["filter_window"])
        row["Static %"] = _text_or_empty(test["static_range"])
        row["Dyn min %"] = _text_or_empty(test["dynamic_min"])
        row["Dyn max %"] = _text_or_empty(test["dynamic_max"])
        row["Steps"] = test["steps"]
        rows.append(row)

    names = ["id", "File name"]
    editable = []
    for column in columns:
        names.append(column["name"])
        editable.append(column["name"])
    names = names + ["Empty fields", "Saved", "Filter pts", "Static %", "Dyn min %", "Dyn max %", "Steps"]
    return pd.DataFrame(rows, columns=names), editable


def save_database_table(edited_table):
    """Store the edited information of the Database tab's table. Nothing is
    stored when a number column holds something else. Returns
    (number of tests changed, list of problems as text)."""
    table = pd.DataFrame(edited_table)
    columns = database.list_info_columns()
    all_values = database.get_all_info_values()

    changes = {}
    problems = []
    for i in range(len(table)):
        row = table.iloc[i]
        test_id = int(row["id"])
        stored = all_values.get(test_id)
        if stored is None:
            continue    # deleted since the table was read
        changed = {}
        for column in columns:
            if column["name"] not in table.columns:
                continue    # added since the table was read
            value, is_valid = read_typed_value(column, row[column["name"]])
            if not is_valid:
                problems.append(f"test #{test_id}: {column['name']} must be a number")
            elif value != stored.get(column["id"]):
                changed[column["id"]] = value
        if len(changed) > 0:
            changes[test_id] = changed

    if len(problems) > 0:
        return 0, problems
    for test_id in changes:
        database.save_info_values(test_id, changes[test_id])
    return len(changes), []
