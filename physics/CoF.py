import warnings
from .utility_functions import Find_minima, Evaluate


def calculate(df, normal_load_correction_factor):
    if normal_load_correction_factor is None:
        df["CoF"] = (df["friction force left"] + df["friction force right"]) / df[
            "normal load"
        ]
    elif normal_load_correction_factor == 0:
        warnings.warn("CoF is not the real CoF. Careful with units.")
        df["CoF"] = df["friction force left"] + df["friction force right"]
    else:

        def calculate_cof_ith_corrected_nl(row):
            NL = max(0, row["normal load"] - normal_load_correction_factor)
            return (row["friction force left"] + row["friction force right"]) / NL

        df["CoF"] = df.apply(calculate_cof_ith_corrected_nl, axis=1)
    return df


def find_minima(df):
    return Find_minima(df, "CoF")


def get_static_and_dynamic_cof(
    df, CoF_minima, static_cof_range, beginning_dynamic_range, ending_dynamic_range
):
    return Evaluate(
        df,
        CoF_minima,
        "CoF",
        static_cof_range,
        beginning_dynamic_range,
        ending_dynamic_range,
    )
