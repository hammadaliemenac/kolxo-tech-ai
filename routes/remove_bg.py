from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse
from rembg import remove, new_session
from PIL import Image, ImageFilter
import io
import numpy as np

# Initialize session
session = new_session("isnet-general-use")
router = APIRouter()

@router.post("/remove-bg")
async def remove_bg(file: UploadFile = File(...)):
    input_bytes = await file.read()
    input_image = Image.open(io.BytesIO(input_bytes)).convert("RGBA")

    # 1. Use Alpha Matting for better edge detection
    # This prevents the "faded" look by calculating foreground/background transitions better
    output = remove(
        input_image, 
        session=session, 
        alpha_matting=True, 
        alpha_matting_foreground_threshold=240, # Keeps more of the object
        alpha_matting_background_threshold=10,  # Is more aggressive with background
        alpha_matting_erode_size=10
    )

    # 2. Refine the Alpha Channel without destroying white pixel data
    img_np = np.array(output)
    
    # Extract the alpha channel
    alpha = img_np[:, :, 3]

    # Create a smoother transition using a slight Gaussian blur on the mask only
    # This fixes "jagged" edges without affecting the RGB color of the object
    mask = Image.fromarray(alpha)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=0.5))
    
    # 3. Boost Alpha Contrast
    # Instead of sqrt (which affects everything), we use a lookup table to 
    # sharpen the edges while keeping the "core" of the object 100% opaque.
    mask_np = np.array(mask)
    mask_np = np.where(mask_np > 128, 255, mask_np * 1.1) # Boost semi-transparent, keep solid solid
    mask_np = np.clip(mask_np, 0, 255).astype(np.uint8)

    # Re-apply the cleaned mask to the original colors
    img_np[:, :, 3] = mask_np
    final_output = Image.fromarray(img_np)

    # Save and return
    buf = io.BytesIO()
    final_output.save(buf, format="PNG")
    buf.seek(0)

    return StreamingResponse(buf, media_type="image/png")