"""The information typed in about a test: reading what the user typed on the
save form and the Database tab's form, the Database tab's tables, and the
forms and tables of the Samples and Materials tabs.

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
    "not_numbers": [column names]}. The names are the column labels."""
    values = {}
    empty = []
    not_numbers = []
    for column in columns:
        value, is_valid = read_typed_value(column, typed.get(column["key"]))
        if not is_valid:
            not_numbers.append(column["label"])
        elif value is None:
            empty.append(column["label"])
        values[column["id"]] = value
    return {"values": values, "empty": empty, "not_numbers": not_numbers}


def _text_or_empty(value):
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value)


def build_database_table():
    """The Database tab's table of tests: one row per saved test, newest
    first. All cells are text. It only shows the tests: they are changed
    with the form above it, because mo.ui.data_editor's cells drop a minus
    sign typed first, which turned -9 into 9."""
    columns = database.list_info_columns()
    all_values = database.get_all_info_values()
    rows = []
    for test in database.list_tests():
        row = {"id": test["id"], "File name": test["file_name"]}
        n_empty = 0
        values = all_values.get(test["id"], {})
        for column in columns:
            text = value_as_text(values.get(column["id"]))
            row[column["label"]] = text
            if text == "":
                n_empty = n_empty + 1
        row["Material"] = _text_or_empty(test["material"])
        row["Empty fields"] = n_empty
        row["Saved"] = _text_or_empty(test["uploaded_at"])[:16]
        row["Filter pts"] = _text_or_empty(test["filter_window"])
        row["Static %"] = _text_or_empty(test["static_range"])
        row["Dyn min %"] = _text_or_empty(test["dynamic_min"])
        row["Dyn max %"] = _text_or_empty(test["dynamic_max"])
        row["Steps"] = test["steps"]
        rows.append(row)

    names = ["id", "File name", "Empty fields"]
    for column in columns:
        names.append(column["label"])
        if column["field"] == "sample":
            names.append("Material")    # read from the sample, so it has no box
    names = names + ["Steps", "Saved", "Filter pts", "Static %", "Dyn min %", "Dyn max %"]
    return pd.DataFrame(rows, columns=names)


def build_column_table():
    """The overview on the "Manage columns" view: one row per information
    column, with how many tests have it filled in."""
    all_values = database.get_all_info_values()
    rows = []
    for column in database.list_info_columns():
        n_filled = 0
        for test_id in all_values:
            if all_values[test_id].get(column["id"]) is not None:
                n_filled = n_filled + 1
        can_change = "Yes"
        if column["protected"]:
            can_change = "No, the app needs it"
        rows.append({
            "Column": column["name"],
            "Unit": column["unit"],
            "Type": column["kind"].capitalize(),
            "Filled in": f"{n_filled} of {len(all_values)} tests",
            "Can be changed": can_change,
        })
    return pd.DataFrame(rows, columns=["Column", "Unit", "Type", "Filled in", "Can be changed"])


def read_list_form(fields, typed):
    """Read the form of the Samples or Materials tab. `fields` is
    database.SAMPLE_FIELDS or MATERIAL_FIELDS, `typed` is {attribute: typed
    text}. Returns (values, list of number boxes holding something else);
    values is {attribute: value or None}."""
    values = {}
    not_numbers = []
    for attribute, name, unit, kind in fields:
        value, is_valid = read_typed_value({"kind": kind}, typed.get(attribute))
        if not is_valid:
            not_numbers.append(name)
        values[attribute] = value
    return values, not_numbers


def _build_list_table(fields, items):
    """One row per sample or material. All cells are text."""
    names = ["id"]
    for attribute, name, unit, kind in fields:
        names.append(database.column_label(name, unit))
    names.append("Tests")

    rows = []
    for item in items:
        row = {"id": item["id"], "Tests": item["n_tests"]}
        for attribute, name, unit, kind in fields:
            row[database.column_label(name, unit)] = _text_or_empty(item[attribute])
        rows.append(row)
    return pd.DataFrame(rows, columns=names)


def build_material_table():
    """The Materials tab's table."""
    return _build_list_table(database.MATERIAL_FIELDS, database.list_materials())


def build_sample_table():
    """The Samples tab's table."""
    return _build_list_table(database.SAMPLE_FIELDS, database.list_samples())


def save_typed_values(test_ids, typed):
    """Store the Database tab's form on the ticked tests. `typed` is
    {column key: typed text}. For one test the form shows all its values, so
    an emptied box clears that value. For several tests the form starts
    empty, so only the boxes filled in are stored. Nothing is stored when a
    number column holds something else. Returns (number of tests saved,
    list of problems as text)."""
    read = read_typed_values(database.list_info_columns(), typed)
    if len(read["not_numbers"]) > 0:
        problems = []
        for label in read["not_numbers"]:
            problems.append(f"{label} must be a number")
        return 0, problems

    values = read["values"]
    if len(test_ids) > 1:
        filled = {}
        for column_id in values:
            if values[column_id] is not None:
                filled[column_id] = values[column_id]
        if len(filled) == 0:
            return 0, ["fill in at least one box"]
        values = filled
    for test_id in test_ids:
        database.save_info_values(test_id, values)
    return len(test_ids), []
