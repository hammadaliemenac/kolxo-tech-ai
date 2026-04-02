from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse
from rembg import remove, new_session
from PIL import Image
import io

session = new_session("isnet-general-use")
router = APIRouter()

@router.post("/remove-bg")
async def remove_bg(file: UploadFile = File(...)):
    input_bytes = await file.read()

    input_image = Image.open(io.BytesIO(input_bytes)).convert("RGBA")

    output = remove(
        input_image,
        session=session,
        alpha_matting=False
    )

    # 🔥 Fix fade issue
    output = output.convert("RGBA")
    pixels = output.load()

    for y in range(output.size[1]):
        for x in range(output.size[0]):
            r, g, b, a = pixels[x, y]

            if a < 180:
                pixels[x, y] = (0, 0, 0, 0)
            else:
                pixels[x, y] = (r, g, b, 255)

    buf = io.BytesIO()
    output.save(buf, format="PNG")
    buf.seek(0)

    return StreamingResponse(buf, media_type="image/png")