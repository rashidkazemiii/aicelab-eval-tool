import glob
import logging
import os
from pathlib import Path
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
from session import state
from parsers import loader

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), data_type: str = "OFT"):
    try:
        # Strip any directory components from the filename for safety
        safe_name = Path(file.filename).name

        # Remove previous uploads before writing the new file
        for old in glob.glob("temp_uploads/*"):
            os.remove(old)

        file_location = f"temp_uploads/{safe_name}"
        with open(file_location, "wb+") as f:
            f.write(await file.read())

        state.file_path = file_location
        state.data_type = data_type
        state.df_raw, state.step_df, state.header = loader.load_data(file_location, data_type)
        state.df_filter = None
        state.df_result = None

        return {"status": "success", "message": f"{safe_name} loaded ({data_type})"}
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return JSONResponse(status_code=400, content={"error": str(e)})
