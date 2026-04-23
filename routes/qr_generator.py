from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import qrcode
import os
import uuid
from fastapi.responses import FileResponse

router = APIRouter()

class QRGeneratorRequest(BaseModel):
    url: str

UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

from fastapi.responses import StreamingResponse
import io

@router.post("/qr-generator/")
def generate_qr(request: QRGeneratorRequest):
    try:
        # Generate QR Code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(request.url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Save the image to a bytes buffer
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        # Return the image as a StreamingResponse
        return StreamingResponse(buf, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
