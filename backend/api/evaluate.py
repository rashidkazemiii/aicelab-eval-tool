import logging
import traceback
import pandas as pd
from fastapi import APIRouter
from fastapi.responses import JSONResponse, Response, HTMLResponse
from session import state
from physics import utility_functions
from config import RESULT_COLUMNS, RESULT_COL_MAP, DEFAULT_STATIC_RANGE, DEFAULT_DYN_MIN, DEFAULT_DYN_MAX

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _cof_minima(df, column):
    m = utility_functions.Find_minima(df, column)
    return m.rename(columns={
        f"-Min {column}": "-Min CoF",
        f"+Min {column}": "+Min CoF",
        f"Min {column}":  "Min CoF",
    })


def _per_cycle_stats(df_eval, minima, static_range, dyn_min, dyn_max):
    return utility_functions.Evaluate(df_eval, minima, "CoF", static_range, dyn_min, dyn_max)


def _aggregate_stats(per_cycle, time_range):
    return {
        "timeRange":        time_range,
        "staticMeanCoF":    per_cycle["staticCoF"].mean(),
        "staticCoFSD_agg":  per_cycle["staticCoF"].std(),
        "staticCoFN_agg":   int(per_cycle["staticCoF"].count()),
        "staticCoFSum_agg": per_cycle["staticCoF"].sum(),
        "staticCoFVar_agg": per_cycle["staticCoF"].var(),
        "dynamicMeanCoF":   per_cycle["dynamicCoF"].mean(),
        "dynamicCoFSD_agg": per_cycle["dynamicCoF"].std(),
        "dynamicCoFN_agg":  int(per_cycle["dynamicCoFn"].sum()),
        "dynamicCoFSum_agg":per_cycle["dynamicCoFsigma"].sum(),
        "dynamicCoFVar_agg":per_cycle["dynamicCoF"].var(),
        "integralTimeRange":time_range,
    }


def _displacement_data(df_filter, neg_times):
    disp_col = next(
        (c for c in ("external displacement", "stroke_filtered", "stroke_shifted", "stroke")
         if c in df_filter.columns),
        None
    )
    if disp_col is None:
        return pd.DataFrame()

    dm = utility_functions.Find_minima(df_filter, disp_col)
    dm = dm.rename(columns={
        "-Min Zeit":          "dispMinZeit_neg",
        f"-Min {disp_col}":   "-Min disp",
        "+Min Zeit":          "dispMinZeit_pos",
        f"+Min {disp_col}":   "+Min disp",
        "Min Zeit":           "dispMinZeit_zero",
        f"Min {disp_col}":    "Min disp",
    }).reset_index(drop=True)

    disp_df = df_filter[["Zeit [s]", disp_col]]
    max_times, max_vals = [], []
    for i in range(len(neg_times) - 1):
        seg = disp_df[
            (disp_df["Zeit [s]"] >= neg_times[i]) &
            (disp_df["Zeit [s]"] <= neg_times[i + 1])
        ]
        if len(seg):
            idx = seg[disp_col].abs().idxmax()
            max_times.append(seg.loc[idx, "Zeit [s]"])
            max_vals.append(seg.loc[idx, disp_col])

    n = len(max_vals)
    dm["dispMaxTime"] = float("nan")
    dm["dispMax"]     = float("nan")
    if n:
        k = min(n, len(dm))
        dm.loc[:k - 1, "dispMaxTime"] = max_times[:k]
        dm.loc[:k - 1, "dispMax"]     = max_vals[:k]

    return dm


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/evaluate")
def evaluate(
    static_cof_range:       float = DEFAULT_STATIC_RANGE,
    beginning_dynamic_range:float = DEFAULT_DYN_MIN,
    ending_dynamic_range:   float = DEFAULT_DYN_MAX,
):
    if state.df_filter is None:
        return JSONResponse(status_code=400, content={"error": "Run calculate first"})
    try:
        column = (
            "CoF_Filtered" if "CoF_Filtered" in state.df_filter.columns else
            "CoF_shifted"  if "CoF_shifted"  in state.df_filter.columns else
            "CoF"
        )

        minima    = _cof_minima(state.df_filter, column)
        df_eval   = state.df_filter.copy()
        if "CoF_shifted" in df_eval.columns:
            df_eval["CoF"] = df_eval["CoF_shifted"]

        per_cycle = _per_cycle_stats(
            df_eval, minima, static_cof_range,
            beginning_dynamic_range, ending_dynamic_range
        )
        agg  = _aggregate_stats(
            per_cycle,
            state.df_filter["Zeit [s]"].max() - state.df_filter["Zeit [s]"].min()
        )
        disp = _displacement_data(state.df_filter, minima["-Min Zeit"].tolist())

        n = len(per_cycle)
        state.df_result = pd.DataFrame(float("nan"), index=range(n), columns=RESULT_COLUMNS)

        for col in per_cycle.columns:
            if col in state.df_result.columns:
                state.df_result[col] = per_cycle[col].values

        m = min(len(minima), n)
        for col in minima.columns:
            if col in state.df_result.columns:
                state.df_result.loc[:m - 1, col] = minima[col].values[:m]

        if n > 0:
            for col, val in agg.items():
                state.df_result.loc[0, col] = val

        d = min(len(disp), n)
        for col in disp.columns:
            if col in state.df_result.columns:
                state.df_result.loc[:d - 1, col] = disp[col].values[:d]

        agg_serializable = {k: (None if pd.isna(v) else v) for k, v in agg.items()
                            if not isinstance(v, pd.Series)}
        return {"status": "success", "cycles": n, "aggregate": agg_serializable}

    except Exception as e:
        logger.error(f"Evaluate failed: {e}\n{traceback.format_exc()}")
        state.last_error = str(e)
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/result/json")
def get_result_json():
    if state.df_result is None:
        return JSONResponse(status_code=400, content={"error": "Run evaluate first"})
    return Response(
        content=state.df_result.to_json(orient="records", double_precision=8),
        media_type="application/json"
    )


@router.get("/result/html")
def get_result_html():
    if state.df_result is None:
        last_err = state.last_error
        msg = f"<p style='color:#c0392b'><b>Last error:</b> {last_err}</p>" if last_err else ""
        return HTMLResponse(content=f"""<!DOCTYPE html><html><head><title>Result</title>
<style>body{{font-family:monospace;padding:40px;background:#f4f6f8;color:#1f2a40}}</style></head>
<body><h2>No results yet</h2>
<p>Run <b>Evaluate</b> on the Analysis page first.</p>{msg}</body></html>""")

    df_view = state.df_result[[k for k, _ in RESULT_COL_MAP]].rename(columns=dict(RESULT_COL_MAP))
    table = df_view.to_html(index=False, border=0, classes="data-table", na_rep="")
    html = f"""<!DOCTYPE html><html><head><title>Result</title>
<style>
  body {{ font-family: monospace; font-size: 12px; padding: 20px; background: #f4f6f8; overflow-x: auto; }}
  h2 {{ color: #1f2a40; }}
  .data-table {{ border-collapse: collapse; background: #fff; white-space: nowrap; }}
  .data-table th {{ background: #1f2a40; color: #fff; padding: 6px 12px; text-align: right; position: sticky; top: 0; }}
  .data-table td {{ padding: 4px 12px; text-align: right; border-bottom: 1px solid #e0e0e0; }}
  .data-table tr:hover td {{ background: #eef2ff; }}
</style></head>
<body><h2>Evaluation Result</h2>{table}</body></html>"""
    return HTMLResponse(content=html)
