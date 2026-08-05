import os
import tempfile
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from ai.pipeline import ArkanaPipeline
from ai.backend.api.schemas import VisualIdentifyResponse
from ai.backend.api.dependencies import get_pipeline

router = APIRouter()

@router.post("/identify", response_model=VisualIdentifyResponse)
async def identify_endpoint(
    image: UploadFile = File(...), 
    pipeline: ArkanaPipeline = Depends(get_pipeline)
):
    """
    Visual identification endpoint.
    Accepts an uploaded image and passes it to the AI visual pipeline.
    """
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file is not an image")

    # Save to a temporary file for PIL processing
    try:
        suffix = os.path.splitext(image.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await image.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Call pipeline
        result = await pipeline.identify_image(tmp_path)
        
        # Cleanup
        os.remove(tmp_path)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Visual identification failed: {str(e)}")
