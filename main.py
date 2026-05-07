from read_files import load
import matplotlib.pyplot as plt
import pandas as pd
from physics import utility_functions

import logging
logging.basicConfig(level=logging.INFO)   #so we can see the logs in the terminal

from fastapi import FastAPI

#1. initialize the FastAPI app
app = FastAPI()

# --- SETTINGS ---
FILE_PATH = "data/OFT07935.txt"   #
DATA_TYPE = "OFT"               # Options: "SRV", "SRV_FSA", "OFT"
FILTER_WINDOW = 25

# 2. Define a "Hello World" root endpoint
@app.get("/")
def read_root():
    return {"message": "Hello World! Your Backend is Live"}

# 3. Define an endpoint to run your logic
@app.get("/analyze")
def analyze_data():
    try:
        # Expected types:
        # df -> pd.DataFrame (main measurement data)
        # step_df -> pd.DataFrame | None (step metadata, may be missing)
        # header -> dict | None (header metadata, may be missing)
        # Your existing loading logic
        df, step_df, header = load.load_data(FILE_PATH, DATA_TYPE)

        # Build processed copies so the original df stays unchanged.
        df_offset = utility_functions.offset(df.copy(), step_df)
        df_filtered = utility_functions.filter(df_offset.copy(), step_df, FILTER_WINDOW)

        # For "Hello World" stage, we return text/data instead of showing a plot
        return {
            "status": "success",
            "rows_loaded": len(df),
            "columns": list(df.columns),
            "message": "Data processed successfully. Ready to send to frontend!"
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}










