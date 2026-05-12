from read_files import load
import matplotlib.pyplot as plt
import pandas as pd
from physics import utility_functions
import json
import logging
import os

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

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
    allow_origins=["http://localhost:5173"],
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
    global latest_file_path

    try:
        # Save uploaded file
        file_location = f"temp_uploads/{file.filename}"

        with open(file_location, "wb+") as file_object:
            file_object.write(await file.read())

        latest_file_path = file_location

        print(f"File saved at: {file_location}")

        # ---------------------------------------------------
        # Load dataframe immediately after upload
        # ---------------------------------------------------
        df, step_df, header = load.load_data(latest_file_path, DATA_TYPE)

        # Optional processing
        df_offset = utility_functions.offset(df.copy(), step_df)
        df_filtered = utility_functions.filter(
            df_offset.copy(),
            step_df,
            FILTER_WINDOW
        )

        # ---------------------------------------------------
        # Return chart data directly
        # ---------------------------------------------------
        return {
            "status": "success",

            "zeit": df_filtered['Zeit [s]'].tolist(),

            "cof_raw": df_offset['CoF'].tolist(),

            "cof_filtered": df_filtered['CoF'].tolist(),

            "metadata": {
                "rows": len(df_filtered),
                "filename": file.filename
            }
        }

    except Exception as e:
        logging.exception("Upload failed")

        return {
            "status": "error",
            "message": str(e)
        }

# ---------------------------------------------------
# Analysis endpoint (KEEP for future use)
# ---------------------------------------------------
@app.get("/analyze")
def analyze_data():

    global latest_file_path

    try:

        if latest_file_path is None:
            return {
                "status": "error",
                "message": "No file uploaded yet"
            }

        df, step_df, header = load.load_data(
            latest_file_path,
            DATA_TYPE
        )

        df_offset = utility_functions.offset(df.copy(), step_df)

        df_filtered = utility_functions.filter(
            df_offset.copy(),
            step_df,
            FILTER_WINDOW
        )

        return {
            "status": "success",

            "zeit": df_filtered['Zeit [s]'].tolist(),

            "cof_raw": df_offset['CoF'].tolist(),

            "cof_filtered": df_filtered['CoF'].tolist(),

            "metadata": {
                "rows": len(df_filtered),
                "filter_window": FILTER_WINDOW
            }
        }

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }