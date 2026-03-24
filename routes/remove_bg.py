from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse
from rembg import remove, new_session
from PIL import Image
import io

session = new_session()
router = APIRouter()

@router.post("/remove-bg")
async def remove_bg(file: UploadFile = File(...)):
    # Read uploaded image
    input_bytes = await file.read()

    # Remove background
    output_bytes = remove(input_bytes, session=session)

    # Return as image
    return StreamingResponse(
        io.BytesIO(output_bytes),
        media_type="image/png"
    )