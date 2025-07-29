import os

from fastapi import APIRouter
from fastapi.responses import FileResponse

from backend.src.constants.properties import IMAGE_PATH

router = APIRouter(prefix="/image", tags=["Image"])

@router.get("/{image_id}")
def get_image(image_id: str):
    file_path = os.path.join(IMAGE_PATH, f"{image_id}.png")
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="image/png")
    return {"error": "File not found!"}