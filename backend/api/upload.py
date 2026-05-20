import logging
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
from session import state
from read_files import load

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), data_type: str = "OFT"):
    try:
        file_location = f"temp_uploads/{file.filename}"
        with open(file_location, "wb+") as f:
            f.write(await file.read())

        state.file_path = file_location
        state.data_type = data_type
        state.df_raw, state.step_df, state.header = load.load_data(file_location, data_type)
        state.df_filter = None
        state.df_result = None

        return {"status": "success", "message": f"{file.filename} loaded ({data_type})"}
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return JSONResponse(status_code=400, content={"error": str(e)})
