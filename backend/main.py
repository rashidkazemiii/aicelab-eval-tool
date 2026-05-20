import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import upload_api, cof_api, stroke_api, export_api

logging.basicConfig(level=logging.INFO)
os.makedirs("temp_uploads", exist_ok=True)

app = FastAPI(title="ICELAB Friction Evaluation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_api.router)
app.include_router(cof_api.router)
app.include_router(stroke_api.router)
app.include_router(export_api.router)


@app.get("/")
def root():
    return {"message": "ICELAB Friction Evaluation API is live"}
