from read_files import load
import matplotlib.pyplot as plt
import pandas as pd
from physics import utility_functions
import json
import logging
import os
logger = logging.getLogger(__name__)
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

# ---------------------------------------------------
# Root endpoint
# ---------------------------------------------------
@app.get("/")
def read_root():
    print("Test");
    return {"message": "Hello World! Your Backend is Live"}
    
    

# ---------------------------------------------------
# Upload endpoint
# ---------------------------------------------------
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    global latest_file_path
    try:
        # 1. Define save path
        file_location = f"temp_uploads/{file.filename}"
        
        # 2. Save the physical file
        with open(file_location, "wb+") as file_object:
            file_object.write(await file.read())

        # 3. Update the global path
        # This ensures 'load_data' will pull the fresh file next time
        latest_file_path = file_location
        
        # 4. Update/Verify the three variables immediately (optional logging)
        df, step_df, header = load.load_data(latest_file_path, DATA_TYPE)
       
        print("OK");
        return {"status": "success", "message": f"{file.filename} is now the active file"}
    
    except Exception as e:
        print(f"Upload failed: {e}")
       
        return {"status": "error", "message": str(e)}