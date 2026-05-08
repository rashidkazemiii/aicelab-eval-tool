from read_files import load
import matplotlib.pyplot as plt
import pandas as pd
from physics import utility_functions
import json
import logging
logging.basicConfig(level=logging.INFO)   #so we can see the logs in the terminal
#2. import FastAPI and CORS middleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

#1. initialize the FastAPI app
app = FastAPI()

# 3. Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Allow requests from your frontend
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)
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
        print(df_filtered.columns)
      

        # For "Hello World" stage, we return text/data instead of showing a plot
       
       # Extract Zeit and Reibungskraft columns 
     # Convert directly without intermediate variables
    
        return {
            "status": "success",
            "zeit": df_filtered['Zeit [s]'].tolist() if 'Zeit [s]' in df_filtered.columns else [],
            "reibungszahl": df_filtered['CoF'].tolist() if 'CoF' in df_filtered.columns else [],
            "metadata": {
                "rows": len(df_filtered),
                "filter_window": FILTER_WINDOW
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}





