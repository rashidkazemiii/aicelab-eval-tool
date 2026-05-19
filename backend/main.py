from read_files import load
import pandas as pd
from physics import utility_functions, CoF as CoF_module
import json
import logging
import os
logger = logging.getLogger(__name__)
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, Response
import io

logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------
# Create upload folder
# ---------------------------------------------------
os.makedirs("temp_uploads", exist_ok=True)

# ---------------------------------------------------
# FastAPI app
# ---------------------------------------------------
app = FastAPI()

# ---------------------------------------------------
# CORS
# ---------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------
# Global variables
# ---------------------------------------------------
latest_file_path = None

DATA_TYPE = "OFT"
FILTER_WINDOW = 25

df_raw = None           # raw data from file, never modified
df_result = None        # working copy: CoF calculated, offset applied, CoF_Filtered added
df_dynamicCoF = None    # result from Evaluate(): dynamic/static CoF per cycle
step_df_global = None
header_global = None

# ---------------------------------------------------
# Root endpoint
# ---------------------------------------------------
@app.get("/")
def read_root():
    return {"message": "Hello World! Your Backend is Live"}


# ---------------------------------------------------
# Upload endpoint
# ---------------------------------------------------
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    global latest_file_path, df_raw, df_result, df_dynamicCoF, step_df_global, header_global
    try:
        file_location = f"temp_uploads/{file.filename}"

        with open(file_location, "wb+") as file_object:
            file_object.write(await file.read())

        latest_file_path = file_location
        df_raw, step_df_global, header_global = load.load_data(latest_file_path, DATA_TYPE)
        df_result = None
        df_dynamicCoF = None

        return {"status": "success", "message": f"{file.filename} is now the active file"}

    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return {"status": "error", "message": str(e)}


# ---------------------------------------------------
# Calculate endpoint — computes CoF from force channels into df_result
# ---------------------------------------------------
@app.post("/calculate")
def calculate():
    global df_result, df_dynamicCoF
    if df_raw is None:
        return JSONResponse(status_code=400, content={"error": "No file uploaded yet"})
    df_result = CoF_module.calculate(df_raw.copy(), None)
    df_result["CoF"] = df_result["CoF"].round(5)
    df_dynamicCoF = None
    return {"status": "success"}


# ---------------------------------------------------
# Data endpoint — returns initial CoF for chart
# ---------------------------------------------------
@app.get("/data")
def get_data():
    if df_result is None:
        return JSONResponse(status_code=400, content={"error": "No calculated data yet"})
    data = df_result[["Zeit [s]", "CoF"]].rename(columns={"Zeit [s]": "zeit", "CoF": "cof"})
    return Response(content=data.to_json(orient="records", double_precision=5), media_type="application/json")


# ---------------------------------------------------
# Offset endpoint — applies offset to df_result
# ---------------------------------------------------
@app.post("/offset")
def apply_offset():
    global df_result
    if df_result is None:
        return JSONResponse(status_code=400, content={"error": "Run calculate first"})
    df_offset = utility_functions.offset(df_result.copy(), None)
    df_result["CoF_shifted"] = df_offset["CoF"].values
    data = df_result[["Zeit [s]", "CoF", "CoF_shifted"]].rename(columns={"Zeit [s]": "zeit", "CoF": "cof", "CoF_shifted": "cof_shifted"})
    return Response(content=data.to_json(orient="records", double_precision=8), media_type="application/json")


# ---------------------------------------------------
# Filter endpoint — adds CoF_Filtered column to df_result
# CoF_Filtered is kept in df_result for minima finding in evaluate
# ---------------------------------------------------
@app.post("/filter")
def apply_filter(window: int = FILTER_WINDOW):
    global df_result
    if df_result is None:
        return JSONResponse(status_code=400, content={"error": "Apply offset first"})
    source_col = "CoF_shifted" if "CoF_shifted" in df_result.columns else "CoF"
    df_result["CoF_Filtered"] = utility_functions.filter_vb_style(df_result[source_col], window).values
    data = df_result[["Zeit [s]", "CoF", "CoF_shifted", "CoF_Filtered"]].rename(columns={"Zeit [s]": "zeit", "CoF": "cof", "CoF_shifted": "cof_shifted", "CoF_Filtered": "filtered"})
    return Response(content=data.to_json(orient="records", double_precision=8), media_type="application/json")


# ---------------------------------------------------
# Evaluate endpoint — finds minima, stores in df_dynamicCoF
# ---------------------------------------------------
@app.post("/evaluate")
def evaluate(
    static_cof_range: float = 10,
    beginning_dynamic_range: float = 20,
    ending_dynamic_range: float = 80
):
    global df_dynamicCoF
    if df_result is None:
        return JSONResponse(status_code=400, content={"error": "Apply offset first"})
    column = "CoF_Filtered" if "CoF_Filtered" in df_result.columns else "CoF"
    minima = utility_functions.Find_minima(df_result, column)

    df_eval = df_result.copy()
    if "CoF_shifted" in df_eval.columns:
        df_eval["CoF"] = df_eval["CoF_shifted"]
    df_dynamicCoF = utility_functions.Evaluate(
        df_eval, minima, "CoF",
        static_cof_range, beginning_dynamic_range, ending_dynamic_range
    )

    return json.loads(df_dynamicCoF.to_json(orient="records", double_precision=15))


# ---------------------------------------------------
# Export endpoint — returns df_result as CSV download
# ---------------------------------------------------
@app.get("/export")
def export_result():
    if df_result is None:
        return JSONResponse(status_code=400, content={"error": "No result to export"})
    df_export = df_result.copy()
    if "CoF" in df_export.columns:
        df_export["CoF"] = df_export["CoF"].apply(lambda x: f"{x:.5f}")
    if "CoF_shifted" in df_export.columns:
        df_export["CoF_shifted"] = df_export["CoF_shifted"].apply(lambda x: f"{x:.15f}")
    if "CoF_Filtered" in df_export.columns:
        df_export["CoF_Filtered"] = df_export["CoF_Filtered"].apply(lambda x: f"{x:.15f}")
    buffer = io.StringIO()
    df_export.to_csv(buffer, index=False, sep=';')
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=df_result.csv"}
    )


# ---------------------------------------------------
# Export dynamic endpoint — returns df_dynamicCoF as CSV download
# ---------------------------------------------------
@app.get("/export/dynamic")
def export_dynamic():
    if df_dynamicCoF is None:
        return JSONResponse(status_code=400, content={"error": "No dynamic CoF data yet. Run evaluate first."})
    buffer = io.StringIO()
    df_dynamicCoF.to_csv(buffer, index=False, sep=';')
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=df_dynamicCoF.csv"}
    )
