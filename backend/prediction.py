"""The AI tab: predicts the friction of a test that is not in the database
yet, from the saved tests that are most like it ("nearest neighbours").

How it works:
1. Every saved test is described by factors: its conditions (normal
   force, ice temperature...), its sample (Ra, Rz...) and the sample's
   material (hardness, thermal conductivity...). The user chooses which
   factors to compare on.
2. For the new test the user types in the same factors.
3. Each saved test gets a distance to the new test. For a number factor
   the difference is divided by how much that factor varies between the
   saved tests (its standard deviation), so newtons and degrees can be
   compared. A list factor (dry/wet...) counts 0 when it is the same and 1
   when not. Distance = square root of the mean of the squared differences,
   so 0 means "the same in every factor".
4. The k closest tests are used. At every velocity, going up and coming
   down, their friction is read off their curves (straight lines between
   their steps) and averaged; a closer test counts more (weight
   1 / (distance + 0.1)).
5. check_quality leaves each saved test out once, predicts it from the
   others and compares with what was measured.

Only saved tests with a stroke (for the velocity) and every chosen factor
filled in are used.
"""

import math

import numpy as np
import pandas as pd

import database

# (key, name, unit, kind, stored on, attribute). "stored on" is the test,
# its sample or the sample's material.
FACTORS = [
    ("normal_force", "Normal force", "N", "number", "test", "normal_force"),
    ("ice_state", "Ice", "", "list", "test", "ice_state"),
    ("temperature", "Chamber temperature", "°C", "number", "test", "temperature"),
    ("humidity", "Humidity", "%", "number", "test", "humidity"),
    ("ice_surface_temp", "Ice surface temperature", "°C", "number", "test", "ice_surface_temp"),
    ("ice_bulk_temp", "Ice bulk temperature", "°C", "number", "test", "ice_bulk_temp"),
    ("ice_unevenness", "Ice unevenness", "µm", "number", "test", "ice_unevenness"),
    ("chamber_state", "Chamber", "", "list", "test", "chamber_state"),
    ("cooling_place", "Sample cooled in", "", "list", "test", "cooling_place"),
    ("cooling_wait", "Time after cooling", "min", "number", "test", "cooling_wait"),
    ("surface_treatment", "Surface treatment", "", "list", "sample", "surface_treatment"),
    ("chamfer", "Chamfer", "", "list", "sample", "chamfer"),
    ("ra", "Ra", "µm", "number", "sample", "ra"),
    ("rz", "Rz", "µm", "number", "sample", "rz"),
    ("rq", "Rq", "µm", "number", "sample", "rq"),
    ("rsk", "Rsk", "", "number", "sample", "rsk"),
    ("rku", "Rku", "", "number", "sample", "rku"),
    ("material", "Material", "", "list", "test", "material"),
    ("density", "Bulk density", "kg/m³", "number", "material", "density"),
    ("hardness", "Hardness", "", "number", "material", "hardness"),
    ("elastic_modulus", "Elastic modulus", "GPa", "number", "material", "elastic_modulus"),
    ("poisson_ratio", "Poisson's ratio", "", "number", "material", "poisson_ratio"),
    ("thermal_conductivity", "Thermal conductivity", "W/(m·K)", "number", "material", "thermal_conductivity"),
    ("specific_heat", "Specific heat", "J/(kg·K)", "number", "material", "specific_heat"),
    ("contact_angle", "Water contact angle", "°", "number", "material", "contact_angle"),
]

# A closer test counts more: weight = 1 / (distance + WEIGHT_OFFSET). The
# offset keeps a test at distance 0 from getting all the weight.
WEIGHT_OFFSET = 0.1


def factor_info(key):
    """The FACTORS line of one key."""
    for factor in FACTORS:
        if factor[0] == key:
            return factor
    raise KeyError(key)


def _clean(value):
    """None for an empty value, otherwise the value (text stripped)."""
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, str):
        value = value.strip()
        if value == "" or value.lower() == "nan":
            return None
    return value


def _friction_points(test_id, stroke_mm):
    """The test's evaluated steps as velocity [m/s], down (True for the
    steps after the fastest one) and the static and sliding friction."""
    results = database.get_step_results(test_id)
    results = results[results["speed"].notna()].reset_index(drop=True)
    columns = ["velocity", "down", "static", "dynamic"]
    if len(results) == 0:
        return pd.DataFrame([], columns=columns)

    # Where the fastest step starts, skipped steps included, the same way
    # as the velocity charts (charts.build_friction_velocity_figures).
    fastest_speed = None
    fastest_start = None
    all_steps = database.get_step_df(test_id)
    if all_steps is not None and "Drehzahl" in all_steps.columns:
        for k in range(len(all_steps)):
            speed = _clean(all_steps["Drehzahl"].iloc[k])
            if speed is None:
                continue
            if fastest_speed is None or float(speed) > fastest_speed:
                fastest_speed = float(speed)
                fastest_start = float(all_steps["Startzeit [s]"].iloc[k])
    if fastest_start is None:
        biggest = 0
        for i in range(len(results)):
            if float(results.loc[i, "speed"]) > float(results.loc[biggest, "speed"]):
                biggest = i
        fastest_start = float(results.loc[biggest, "start"])

    rows = []
    for i in range(len(results)):
        rows.append({
            "velocity": 2 * (stroke_mm / 1000.0) * float(results.loc[i, "speed"]) / 60.0,
            "down": float(results.loc[i, "start"]) > fastest_start + 1e-6,
            "static": float(results.loc[i, "static_mean"]),
            "dynamic": float(results.loc[i, "dynamic_mean"]),
        })
    return pd.DataFrame(rows, columns=columns)


def load_saved_tests():
    """Every saved test with a stroke and friction per step: a list of
    {"id", "file_name", "sample", "factors": {key: value or None},
    "points": the table from _friction_points, "curves": from _make_curves}."""
    found = []
    db = database.SessionLocal()
    try:
        samples = {}
        for r in db.query(database.Sample).all():
            samples[r.name] = r
        materials = {}
        for r in db.query(database.Material).all():
            materials[r.name] = r
        for test in db.query(database.Test).order_by(database.Test.id).all():
            factors = {}
            for key, name, unit, kind, stored_on, attribute in FACTORS:
                value = None
                if stored_on == "test":
                    value = getattr(test, attribute)
                elif stored_on == "sample" and test.sample in samples:
                    value = getattr(samples[test.sample], attribute)
                elif stored_on == "material" and test.material in materials:
                    value = getattr(materials[test.material], attribute)
                factors[key] = _clean(value)
            found.append({
                "id": test.id, "file_name": test.file_name, "sample": test.sample,
                "stroke_mm": test.stroke_mm, "factors": factors,
            })
    finally:
        db.close()

    tests = []
    for test in found:
        if test["stroke_mm"] is None:
            continue
        points = _friction_points(test["id"], float(test["stroke_mm"]))
        if len(points) == 0:
            continue
        test["points"] = points
        test["curves"] = _make_curves(points)
        tests.append(test)
    return tests


def filled_counts(tests):
    """{factor key: how many of `tests` have it filled in}."""
    counts = {}
    for factor in FACTORS:
        counts[factor[0]] = 0
        for test in tests:
            if test["factors"][factor[0]] is not None:
                counts[factor[0]] = counts[factor[0]] + 1
    return counts


def seen_values(tests, key):
    """The different values of a list factor in `tests`, sorted."""
    values = []
    for test in tests:
        value = test["factors"][key]
        if value is not None and str(value) not in values:
            values.append(str(value))
    values.sort()
    return values


def usable_tests(tests, keys):
    """The tests that have every factor in `keys` filled in."""
    usable = []
    for test in tests:
        complete = True
        for key in keys:
            if test["factors"][key] is None:
                complete = False
        if complete:
            usable.append(test)
    return usable


def _spreads(tests, keys):
    """{number factor key: its standard deviation in `tests`}, None when it
    does not vary (then it can't tell the tests apart)."""
    spreads = {}
    for key in keys:
        if factor_info(key)[3] != "number":
            continue
        values = []
        for test in tests:
            values.append(float(test["factors"][key]))
        spread = float(np.std(values))
        if spread < 1e-12:
            spreads[key] = None
        else:
            spreads[key] = spread
    return spreads


def distance(new_factors, test_factors, keys, spreads):
    """How different a saved test is from the new test (see the top of this
    file). 0 = the same in every factor."""
    total = 0.0
    for key in keys:
        if factor_info(key)[3] == "number":
            if spreads[key] is None:
                difference = 0.0
            else:
                difference = (float(new_factors[key]) - float(test_factors[key])) / spreads[key]
        else:
            if str(new_factors[key]).strip().lower() == str(test_factors[key]).strip().lower():
                difference = 0.0
            else:
                difference = 1.0
        total = total + difference * difference
    return math.sqrt(total / len(keys))


def _make_curves(points):
    """A test's curves, made once so reading them is quick: {(down,
    "static" or "dynamic"): (velocities, values)}, sorted by velocity."""
    curves = {}
    for down in [False, True]:
        part = points[points["down"] == down]
        for column in ["static", "dynamic"]:
            if len(part) == 0:
                curves[(down, column)] = None
                continue
            # The same velocity twice in one direction: use their mean
            mean = part.groupby("velocity", as_index=False)[column].mean().sort_values("velocity")
            curves[(down, column)] = (mean["velocity"].to_numpy(), mean[column].to_numpy())
    return curves


def _curve_value(curves, down, velocity, column):
    """The friction of one test's curve at `velocity`, read off the straight
    lines between its steps. None outside the velocities it was tested at."""
    curve = curves[(down, column)]
    if curve is None:
        return None
    velocities, values = curve
    if velocity < velocities[0] - 1e-9 or velocity > velocities[-1] + 1e-9:
        return None
    return float(np.interp(velocity, velocities, values))


def combine_curves(neighbours):
    """The weighted mean curve of `neighbours` (list of {"test", "weight"}):
    one row per direction and velocity, with the lowest and highest value of
    the tests used, and how many tests reached that velocity."""
    rows = []
    for down in [False, True]:
        velocities = []
        for neighbour in neighbours:
            points = neighbour["test"]["points"]
            for value in points[points["down"] == down]["velocity"]:
                rounded = round(float(value), 4)
                if rounded not in velocities:
                    velocities.append(rounded)
        velocities.sort()
        for velocity in velocities:
            row = {"down": down, "velocity": velocity}
            for column in ["static", "dynamic"]:
                weighted_sum = 0.0
                weight_sum = 0.0
                values = []
                for neighbour in neighbours:
                    value = _curve_value(neighbour["test"]["curves"], down, velocity, column)
                    if value is None:
                        continue
                    weighted_sum = weighted_sum + neighbour["weight"] * value
                    weight_sum = weight_sum + neighbour["weight"]
                    values.append(value)
                if weight_sum == 0:
                    row[column] = None
                    row[column + "_low"] = None
                    row[column + "_high"] = None
                else:
                    row[column] = weighted_sum / weight_sum
                    row[column + "_low"] = min(values)
                    row[column + "_high"] = max(values)
                row["n_tests"] = len(values)
            rows.append(row)
    return pd.DataFrame(rows, columns=[
        "down", "velocity", "static", "static_low", "static_high",
        "dynamic", "dynamic_low", "dynamic_high", "n_tests",
    ])


def _nearest(new_factors, tests, keys, k):
    """The k tests closest to `new_factors`, as a list of {"test",
    "distance", "weight"} with the weights adding up to 1."""
    spreads = _spreads(tests, keys)
    scored = []
    for test in tests:
        scored.append((distance(new_factors, test["factors"], keys, spreads), test["id"], test))
    scored.sort(key=_first_two)
    neighbours = []
    for d, test_id, test in scored[:k]:
        neighbours.append({"test": test, "distance": d, "weight": 1.0 / (d + WEIGHT_OFFSET)})
    total = 0.0
    for neighbour in neighbours:
        total = total + neighbour["weight"]
    for neighbour in neighbours:
        neighbour["weight"] = neighbour["weight"] / total
    return neighbours


def _first_two(item):
    return (item[0], item[1])


def outside_saved_range(new_factors, tests, keys):
    """The factors where the new test is unlike every saved test, as text:
    a number outside their lowest to highest value, or a list value none of
    them has. A prediction there is a guess."""
    warnings = []
    for key in keys:
        key_, name, unit, kind, stored_on, attribute = factor_info(key)
        if kind == "number":
            values = []
            for test in tests:
                values.append(float(test["factors"][key]))
            value = float(new_factors[key])
            if value < min(values) - 1e-12 or value > max(values) + 1e-12:
                warnings.append(f"{name} {value:g} {unit} (saved tests: {min(values):g} to {max(values):g})".replace("  ", " "))
        else:
            found = False
            for test in tests:
                if str(test["factors"][key]).strip().lower() == str(new_factors[key]).strip().lower():
                    found = True
            if not found:
                warnings.append(f"{name} '{new_factors[key]}' (no saved test has it)")
    return warnings


def predict(new_factors, tests, keys, k):
    """Predict the new test. Returns {"neighbours", "curve", "outside",
    "n_usable"}. Raises ValueError when no saved test can be used."""
    if len(keys) == 0:
        raise ValueError("choose at least one factor to compare on")
    usable = usable_tests(tests, keys)
    if len(usable) == 0:
        raise ValueError("no saved test has all the chosen factors filled in")
    neighbours = _nearest(new_factors, usable, keys, k)
    return {
        "neighbours": neighbours,
        "curve": combine_curves(neighbours),
        "outside": outside_saved_range(new_factors, usable, keys),
        "n_usable": len(usable),
    }


def _mean_error(test, curve):
    """Mean difference between a test's measured steps and a predicted
    curve: (static, sliding), or (None, None) when no step can be compared."""
    static_errors = []
    dynamic_errors = []
    points = test["points"]
    for i in range(len(points)):
        down = bool(points["down"].iloc[i])
        velocity = float(points["velocity"].iloc[i])
        for column, errors in [("static", static_errors), ("dynamic", dynamic_errors)]:
            predicted = _curve_value_from_combined(curve, down, velocity, column)
            if predicted is not None:
                errors.append(abs(predicted - float(points[column].iloc[i])))
    if len(static_errors) == 0:
        return None, None
    return float(np.mean(static_errors)), float(np.mean(dynamic_errors))


def _curve_value_from_combined(curve, down, velocity, column):
    """A value of a combine_curves table at `velocity`."""
    part = curve[(curve["down"] == down) & curve[column].notna()]
    if len(part) == 0:
        return None
    part = part.sort_values("velocity")
    velocities = part["velocity"].to_numpy()
    if velocity < velocities[0] - 1e-9 or velocity > velocities[-1] + 1e-9:
        return None
    return float(np.interp(velocity, velocities, part[column].to_numpy()))


def check_quality(tests, keys, k):
    """Leave each usable test out once, predict it from the others, and
    compare with what was measured. Also does the same with the plain mean
    of all the other tests, which ignores the factors: when the prediction
    is not better than that, the chosen factors don't help (yet).
    Returns {"n_tests", "static", "dynamic", "static_plain",
    "dynamic_plain"} (mean differences in friction), or raises ValueError
    with fewer than 2 usable tests."""
    usable = usable_tests(tests, keys)
    if len(usable) < 2:
        raise ValueError("at least 2 saved tests with all the chosen factors are needed")
    errors = {"static": [], "dynamic": [], "static_plain": [], "dynamic_plain": []}
    for test in usable:
        others = []
        for other in usable:
            if other["id"] != test["id"]:
                others.append(other)
        neighbours = _nearest(test["factors"], others, keys, k)
        static, dynamic = _mean_error(test, combine_curves(neighbours))
        everyone = []
        for other in others:
            everyone.append({"test": other, "weight": 1.0})
        static_plain, dynamic_plain = _mean_error(test, combine_curves(everyone))
        if static is None or static_plain is None:
            continue
        errors["static"].append(static)
        errors["dynamic"].append(dynamic)
        errors["static_plain"].append(static_plain)
        errors["dynamic_plain"].append(dynamic_plain)
    if len(errors["static"]) == 0:
        raise ValueError("no test could be compared: their velocities don't overlap")
    result = {"n_tests": len(errors["static"])}
    for name in errors:
        result[name] = float(np.mean(errors[name]))
    return result
