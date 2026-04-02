from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse
from rembg import remove, new_session
from PIL import Image
import io

# session = new_session("isnet-general-use")
session = new_session("u2net_human_seg")
router = APIRouter()

@router.post("/remove-bg")
async def remove_bg(file: UploadFile = File(...)):
    input_bytes = await file.read()

    input_image = Image.open(io.BytesIO(input_bytes)).convert("RGB")

    output = remove(
        input_image,
        session=session,
        alpha_matting=True,
        alpha_matting_foreground_threshold=240,
        alpha_matting_background_threshold=10,
        alpha_matting_erode_size=10
    )

    buf = io.BytesIO()
    output.save(buf, format="PNG")
    buf.seek(0)

    return StreamingResponse(buf, media_type="image/png")