from read_files import load
import pandas as pd
from physics import utility_functions, CoF as CoF_module
import json
import logging
import os
logger = logging.getLogger(__name__)
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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

df_raw = None
df_calc = None
df_offset = None
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
    global latest_file_path, df_raw, df_calc, df_offset, step_df_global, header_global
    try:
        file_location = f"temp_uploads/{file.filename}"

        with open(file_location, "wb+") as file_object:
            file_object.write(await file.read())

        latest_file_path = file_location
        df_raw, step_df_global, header_global = load.load_data(latest_file_path, DATA_TYPE)
        df_calc = None
        df_offset = None

        return {"status": "success", "message": f"{file.filename} is now the active file"}

    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return {"status": "error", "message": str(e)}


# ---------------------------------------------------
# Calculate endpoint — computes CoF from force channels into df_calc
# ---------------------------------------------------
@app.post("/calculate")
def calculate():
    global df_calc
    if df_raw is None:
        return JSONResponse(status_code=400, content={"error": "No file uploaded yet"})
    df_calc = CoF_module.calculate(df_raw.copy(), None)
    return {"status": "success"}


# ---------------------------------------------------
# Data endpoint — returns calculated CoF for initial chart
# ---------------------------------------------------
@app.get("/data")
def get_data():
    if df_calc is None:
        return JSONResponse(status_code=400, content={"error": "No calculated data yet"})
    data = df_calc[["Zeit [s]", "CoF"]].rename(columns={"Zeit [s]": "zeit", "CoF": "cof"})
    return json.loads(data.to_json(orient="records"))


# ---------------------------------------------------
# Offset endpoint
# ---------------------------------------------------
@app.post("/offset")
def apply_offset():
    global df_offset
    if df_calc is None:
        return JSONResponse(status_code=400, content={"error": "Run calculate first"})
    df_offset = utility_functions.offset(df_calc.copy(), step_df_global)
    data = df_offset[["Zeit [s]", "CoF"]].rename(columns={"Zeit [s]": "zeit", "CoF": "offset"})
    return json.loads(data.to_json(orient="records"))


# ---------------------------------------------------
# Filter endpoint — applies filter on top of df_offset
# Returns both offset series and filtered series
# ---------------------------------------------------
@app.post("/filter")
def apply_filter(window: int = FILTER_WINDOW):
    if df_offset is None:
        return JSONResponse(status_code=400, content={"error": "Apply offset first"})
    df_filtered = utility_functions.filter(df_offset.copy(), step_df_global, window)
    data = df_offset[["Zeit [s]", "CoF"]].copy().rename(columns={"Zeit [s]": "zeit", "CoF": "offset"})
    data["filtered"] = df_filtered["CoF"].values
    return json.loads(data.to_json(orient="records"))
