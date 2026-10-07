"""A small prediction model for the AI tab: learns how the test conditions
change the static and sliding (dynamic) CoF, from the saved tests the user
picks, and predicts the CoF - and its spread - for new conditions.

One training row = one evaluated step of one saved test:
    inputs : the test's temperature, humidity and material (typed in by
             hand), its stroke (from the file header, or typed in), and for
             the step itself: its speed (Drehzahl) and whether the speed is
             going down (the step comes after the test's fastest step)
    outputs: the step's static and dynamic mean CoF, and their standard
             deviations (so a prediction can be drawn with error bars)
    weight : the step's number of cycles (Static N) - a step measured over
             48 cycles is more reliable than one over 20, so it counts more
Steps without numbers (skipped as noisy, or no cycles) are left out.

The model is a weighted linear regression (least squares, numpy only), one
per output, all with the same inputs:
    value = b0 + b1 * temperature + b2 * humidity + b3 * stroke
              + b4 * log10(speed) + b5 * going_down
              + one extra number per material
Speed goes in as log10(speed) because friction usually changes with the
logarithm of the sliding speed, not with the speed itself. going_down is 0
for the steps up to the fastest one and 1 after it, so the model can learn
that the curve differs on the way down. The material is a word, so it
becomes one 0/1 column per material ("one-hot"); the first material
(alphabetically) is the reference and has no column of its own.

The trained model is a plain dict (numbers and lists only), saved as JSON
next to the database so it is still there after a restart.
"""

import json
import math
import os

import numpy as np
import pandas as pd

import database

# Bumped whenever the model's layout changes, so an older saved model is
# ignored (it would not have the newer parts) instead of breaking Predict.
MODEL_VERSION = 2

ALL_FEATURES = ["temperature", "humidity", "material", "stroke_mm", "speed", "going_down"]
FEATURE_LABELS = {
    "temperature": "Temperature [deg C]",
    "humidity": "Humidity [%]",
    "material": "Material",
    "stroke_mm": "Stroke [mm]",
    "speed": "Speed [U/min]",
    "going_down": "Speed going up / down",
}
# The ones the user types in per test; speed and going_down come from the
# steps themselves.
TEST_FEATURES = ["temperature", "humidity", "material", "stroke_mm"]

TARGETS = ["static_cof", "dynamic_cof", "static_sd", "dynamic_sd"]
TARGET_LABELS = {
    "static_cof": "Static CoF",
    "dynamic_cof": "Dynamic CoF",
    "static_sd": "Static std dev",
    "dynamic_sd": "Dynamic std dev",
}
# The accuracy check is done for the means, the numbers that matter most.
MEAN_TARGETS = ["static_cof", "dynamic_cof"]

_MODEL_PATH = os.path.join(os.path.dirname(__file__), "ai_model.json")

# A step's time range in the results ("60.0-80.0") is matched to its row in
# the step table by start and end time, within this many seconds.
_STEP_MATCH_TOLERANCE_S = 0.05


def _parse_time_range(text_range):
    """(start, end) from a results time range like "60.0-80.0", or None."""
    if not text_range:
        return None
    # older rows used an en dash as the separator
    parts = str(text_range).replace("–", "-").split("-")
    if len(parts) != 2:
        return None
    try:
        return float(parts[0]), float(parts[1])
    except ValueError:
        return None


def going_down_flags(speeds):
    """For a list of step speeds in test order: 0 for each step up to and
    including the first fastest one, 1 for every step after it."""
    fastest_index = 0
    for k in range(len(speeds)):
        if speeds[k] > speeds[fastest_index]:
            fastest_index = k
    flags = []
    for k in range(len(speeds)):
        if k <= fastest_index:
            flags.append(0)
        else:
            flags.append(1)
    return flags


def build_training_table(test_ids):
    """One row per evaluated step of the given saved tests, with the inputs,
    outputs and weight described at the top of this file. Values that are
    not known are NaN / None."""
    rows = []
    db = database.SessionLocal()
    try:
        for test_id in test_ids:
            test = db.query(database.Test).filter(database.Test.id == test_id).first()
            if test is None:
                continue
            steps = (
                db.query(database.Step).filter(database.Step.test_id == test_id)
                .order_by(database.Step.step_index).all()
            )
            results = db.query(database.Result).filter(database.Result.test_id == test_id).all()

            # When the test's fastest step starts - every step after it is
            # "going down". Taken from ALL steps, skipped ones included, so a
            # fastest step that was skipped as noisy still counts.
            fastest_speed = None
            fastest_start = None
            for step in steps:
                if step.speed is None:
                    continue
                if fastest_speed is None or step.speed > fastest_speed:
                    fastest_speed = step.speed
                    fastest_start = step.start_time

            for result in results:
                if result.static_mean_cof is None or result.dynamic_mean_cof is None:
                    continue
                time_range = _parse_time_range(result.time_range)
                if time_range is None:
                    continue
                speed = None
                for step in steps:
                    same_start = abs(step.start_time - time_range[0]) <= _STEP_MATCH_TOLERANCE_S
                    same_end = abs(step.end_time - time_range[1]) <= _STEP_MATCH_TOLERANCE_S
                    if same_start and same_end:
                        speed = step.speed
                        break
                going_down = None
                if fastest_start is not None:
                    if time_range[0] > fastest_start + _STEP_MATCH_TOLERANCE_S:
                        going_down = 1
                    else:
                        going_down = 0
                weight = result.static_n
                if weight is None or weight <= 0:
                    weight = 1
                rows.append({
                    "test_id": test.id,
                    "file_name": test.file_name,
                    "temperature": test.temperature,
                    "humidity": test.humidity,
                    "material": test.material,
                    "stroke_mm": test.stroke_mm,
                    "speed": speed,
                    "going_down": going_down,
                    "static_cof": result.static_mean_cof,
                    "dynamic_cof": result.dynamic_mean_cof,
                    "static_sd": result.static_sd,
                    "dynamic_sd": result.dynamic_sd,
                    "weight": float(weight),
                })
    finally:
        db.close()
    columns = ["test_id", "file_name", "temperature", "humidity", "material", "stroke_mm",
               "speed", "going_down", "static_cof", "dynamic_cof", "static_sd", "dynamic_sd",
               "weight"]
    return pd.DataFrame(rows, columns=columns)


def usable_rows(table, features):
    """Only the rows where every chosen input and every output is known
    (and the speed, when used, is above 0 - log10 needs that)."""
    keep = []
    for i in range(len(table)):
        row = table.iloc[i]
        ok = True
        for name in features + TARGETS:
            value = row[name]
            if value is None:
                ok = False
            elif name == "material":
                if str(value).strip() == "":
                    ok = False
            elif pd.isna(value):
                ok = False
            elif name == "speed" and float(value) <= 0:
                ok = False
        keep.append(ok)
    return table[keep].reset_index(drop=True)


def _design_matrix(rows, features, materials):
    """The numbers the regression works on: a column of 1s (the constant
    b0), one column per number input, and one 0/1 column per material
    except the first."""
    columns = []
    names = []
    columns.append(np.ones(len(rows)))
    names.append("constant")
    for name in features:
        if name == "material":
            for material in materials[1:]:
                is_this = []
                for value in rows["material"]:
                    if str(value).strip() == material:
                        is_this.append(1.0)
                    else:
                        is_this.append(0.0)
                columns.append(np.array(is_this))
                names.append("material = " + material)
        elif name == "speed":
            columns.append(np.log10(rows["speed"].astype(float).to_numpy()))
            names.append("log10(speed)")
        else:
            columns.append(rows[name].astype(float).to_numpy())
            names.append(name)
    return np.column_stack(columns), names


def _fit(rows, features, materials):
    """Weighted least-squares coefficients for every output. Weighting a
    row by w is the same as multiplying that row of the equations by
    sqrt(w) and then solving normally."""
    x, names = _design_matrix(rows, features, materials)
    root_weight = np.sqrt(rows["weight"].astype(float).to_numpy())
    x_weighted = x * root_weight[:, None]
    coefficients = {}
    for target in TARGETS:
        y = rows[target].astype(float).to_numpy()
        solution = np.linalg.lstsq(x_weighted, y * root_weight, rcond=None)[0]
        coefficients[target] = list(solution)
    return coefficients, names


def _predict_rows(coefficients, rows, features, materials):
    x, _ = _design_matrix(rows, features, materials)
    out = {}
    for target in TARGETS:
        out[target] = x @ np.array(coefficients[target])
    return out


def _leave_one_test_out_error(rows, features, materials):
    """How well the model predicts a test it has NOT seen: for every test,
    train on all the other tests, predict this one, and average the
    absolute errors. Also the same error for simply guessing the average
    of the other tests, to compare against. None when there are fewer than
    2 tests."""
    test_ids = sorted(rows["test_id"].unique())
    if len(test_ids) < 2:
        return None
    errors = {}
    guess_errors = {}
    for target in MEAN_TARGETS:
        errors[target] = []
        guess_errors[target] = []
    for test_id in test_ids:
        train_rows = rows[rows["test_id"] != test_id]
        test_rows = rows[rows["test_id"] == test_id]
        coefficients, _ = _fit(train_rows, features, materials)
        predicted = _predict_rows(coefficients, test_rows, features, materials)
        for target in MEAN_TARGETS:
            measured = test_rows[target].astype(float).to_numpy()
            average = train_rows[target].astype(float).mean()
            for k in range(len(measured)):
                errors[target].append(abs(predicted[target][k] - measured[k]))
                guess_errors[target].append(abs(average - measured[k]))
    result = {}
    for target in MEAN_TARGETS:
        result[target] = {
            "model": float(np.mean(errors[target])),
            "average_guess": float(np.mean(guess_errors[target])),
        }
    return result


def train(table, features):
    """Train on the usable rows of `table` with the chosen `features`.
    Returns the model dict. Raises ValueError when there is not enough data."""
    if len(features) == 0:
        raise ValueError("choose at least one input parameter")
    rows = usable_rows(table, features)
    n_tests = len(rows["test_id"].unique())
    if len(rows) < len(features) + 2:
        raise ValueError(
            f"only {len(rows)} usable steps (from {n_tests} tests) - fill in the "
            "parameters of more tests, or use fewer inputs"
        )
    materials = []
    if "material" in features:
        for value in rows["material"]:
            name = str(value).strip()
            if name not in materials:
                materials.append(name)
        materials.sort()
    coefficients, names = _fit(rows, features, materials)
    ranges = {}
    for name in features:
        if name != "material":
            ranges[name] = [float(rows[name].min()), float(rows[name].max())]
    return {
        "version": MODEL_VERSION,
        "features": list(features),
        "materials": materials,
        "coefficient_names": names,
        "coefficients": coefficients,
        "ranges": ranges,
        "n_rows": int(len(rows)),
        "n_tests": int(n_tests),
        "n_rows_left_out": int(len(table) - len(rows)),
        "test_ids": [int(t) for t in sorted(rows["test_id"].unique())],
        "error": _leave_one_test_out_error(rows, features, materials),
    }


def predict(model, inputs):
    """Predicted {"static_cof", "dynamic_cof", "static_sd", "dynamic_sd"}
    for one set of `inputs` ({feature name: value}). A standard deviation
    can not be below 0, so a negative one is shown as 0. Raises ValueError
    on a missing or unknown value."""
    row = {"test_id": 0}
    for name in model["features"]:
        value = inputs.get(name)
        if value is None or (name != "material" and pd.isna(value)):
            raise ValueError(f"{FEATURE_LABELS[name]} is missing")
        if name == "material":
            value = str(value).strip()
            if value not in model["materials"]:
                raise ValueError(f"the model does not know the material '{value}'")
        if name == "speed" and float(value) <= 0:
            raise ValueError("speed must be above 0")
        row[name] = value
    rows = pd.DataFrame([row])
    predicted = _predict_rows(model["coefficients"], rows, model["features"], model["materials"])
    out = {}
    for target in TARGETS:
        value = float(predicted[target][0])
        if target in ("static_sd", "dynamic_sd") and value < 0:
            value = 0.0
        out[target] = value
    return out


def outside_training_range(model, inputs):
    """Names of the number inputs that lie outside what the model was
    trained on - a prediction there is a guess (extrapolation)."""
    outside = []
    for name, value_range in model["ranges"].items():
        value = float(inputs[name])
        if value < value_range[0] or value > value_range[1]:
            outside.append(FEATURE_LABELS[name])
    return outside


def coefficients_table(model):
    """The coefficients as a table: how much each input changes each output."""
    table = pd.DataFrame({"Term": model["coefficient_names"]})
    for target in TARGETS:
        table[TARGET_LABELS[target]] = model["coefficients"][target]
    return table


def save_model(model):
    with open(_MODEL_PATH, "w", encoding="utf-8") as f:
        json.dump(model, f, indent=1)


def load_model():
    """The last trained model, or None if there is none, it is broken, or
    it was saved by an older version of this file."""
    try:
        with open(_MODEL_PATH, "r", encoding="utf-8") as f:
            model = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    if model.get("version") != MODEL_VERSION:
        return None
    return model


def to_number(value):
    """A typed-in cell as a float, or None when it is empty / not a number.
    A decimal comma is accepted."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        if isinstance(value, float) and math.isnan(value):
            return None
        return float(value)
    text = str(value).strip().replace(",", ".")
    if text == "" or text.lower() in ("nan", "none"):
        return None
    try:
        return float(text)
    except ValueError:
        return None
