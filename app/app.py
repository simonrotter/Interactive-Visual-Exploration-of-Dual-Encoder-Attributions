import os
from PIL import Image
from typing import List, Optional
from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import httpx
from pydantic import BaseModel, Field
import base64
from io import BytesIO

from token_merge import Merge_Type, rule_based_token_converter
from part_of_speech import analyze_pos

from fastapi.responses import FileResponse

# python -m uvicorn app:app --host 0.0.0.0 --port 80

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow everything for testing
    allow_credentials=True, 
    allow_methods=["*"],
    allow_headers=["*"], 
)

# Configuration for external attribution API
ATTRIBUTION_API_URL = os.getenv("ATTRIBUTION_API_URL", "http://localhost:8000")
ATTRIBUTION_API_TIMEOUT = 30.0

# Create image cache directory if it doesn't exist
os.makedirs("image_cache", exist_ok=True)


class TextAttributionRequest(BaseModel):
    text_a: str
    text_b: str


class TextAttributionResponse(BaseModel):
    text_a: List[str]
    text_b: List[str]
    tokens_a: List[str]
    tokens_b: List[str]
    attributions: List[List[float]]


class ImageAttributionRequest(BaseModel):
    image_base64: str
    caption: str


class ImageAttributionResponse(BaseModel):
    caption: str
    tokens: List[str]
    attributions: List[float]


async def get_text_attribution(text_a: str, text_b: str) -> TextAttributionResponse:
    """
    Call external API to get text attribution
    """
    async with httpx.AsyncClient(timeout=ATTRIBUTION_API_TIMEOUT) as client:
        try:
            response = await client.post(
                f"{ATTRIBUTION_API_URL}/api/text-attribution",
                json={"text_a": text_a, "text_b": text_b}
            )
            response.raise_for_status()
            data = response.json()
            return TextAttributionResponse(**data)
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get attribution from API: {str(e)}"
            )


async def get_image_attribution(image_base64: str, caption: str) -> ImageAttributionResponse:
    """
    Call external API to get image attribution
    """
    async with httpx.AsyncClient(timeout=ATTRIBUTION_API_TIMEOUT) as client:
        try:
            response = await client.post(
                f"{ATTRIBUTION_API_URL}/api/image-attribution",
                json={"image_base64": image_base64, "caption": caption}
            )
            response.raise_for_status()
            data = response.json()
            return ImageAttributionResponse(**data)
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get image attribution from API: {str(e)}"
            )


# =============================================================================
# TEXT ATTRIBUTION ENDPOINTS
# =============================================================================

@app.post("/api/attribution")
async def get_attribution(request: TextAttributionRequest):
    """
    Get attribution for a pair of texts
    """
    result = await get_text_attribution(request.text_a, request.text_b)
    
    return {
        "text_a": result.text_a,
        "text_b": result.text_b,
        "tokens_a": result.tokens_a,
        "tokens_b": result.tokens_b,
        "attributions": result.attributions
    }


@app.post("/api/merge-words")
async def merge_tokens(request: TextAttributionRequest):
    """
    Get attribution merged at word level
    """
    result = await get_text_attribution(request.text_a, request.text_b)
    
    return rule_based_token_converter({
        "tokens_a": result.tokens_a,
        "tokens_b": result.tokens_b,
        "attributions": result.attributions
    }, Merge_Type.Words)


@app.post("/api/merge-word-combinations")
async def merge_combination_tokens(request: TextAttributionRequest):
    """
    Get attribution merged at word combination level
    """
    result = await get_text_attribution(request.text_a, request.text_b)
    
    return rule_based_token_converter({
        "tokens_a": result.tokens_a,
        "tokens_b": result.tokens_b,
        "attributions": result.attributions
    }, Merge_Type.Wordcombinations)


@app.post("/api/pos")
async def pos_analysis(request: TextAttributionRequest):
    """
    Get part-of-speech analysis with word-level attribution
    """
    result = await get_text_attribution(request.text_a, request.text_b)
    
    merged = rule_based_token_converter({
        "tokens_a": result.tokens_a,
        "tokens_b": result.tokens_b,
        "attributions": result.attributions
    }, Merge_Type.Words)
    
    return analyze_pos(merged)


@app.post("/api/pos-combinations")
async def pos_combi(request: TextAttributionRequest):
    """
    Get part-of-speech analysis with word combination attribution
    """
    result = await get_text_attribution(request.text_a, request.text_b)
    
    merged = rule_based_token_converter({
        "tokens_a": result.tokens_a,
        "tokens_b": result.tokens_b,
        "attributions": result.attributions
    }, Merge_Type.Wordcombinations)
    
    return analyze_pos(merged)


# =============================================================================
# IMAGE ATTRIBUTION ENDPOINTS
# =============================================================================

@app.post("/api/image-attribution")
async def image_attribution_base64(request: ImageAttributionRequest):
    """
    Get attribution for an image with caption
    Accepts base64 encoded image
    """
    result = await get_image_attribution(request.image_base64, request.caption)
    
    # Save image to cache for serving
    try:
        image_data = base64.b64decode(request.image_base64)
        image = Image.open(BytesIO(image_data))
        image_id = hash(request.image_base64) % 1000000  # Simple hash for caching
        image_path = f"image_cache/temp_image_{image_id}.png"
        image.save(image_path)
        
        return analyze_pos({
            "caption": result.caption,
            "tokens": result.tokens,
            "attributions": result.attributions,
            "image_url": f"/image/{image_id}"
        })
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to process image: {str(e)}"
        )


@app.post("/api/image-attribution-file")
async def image_attribution_file(
    image: UploadFile = File(...),
    caption: str = Form(...)
):
    """
    Get attribution for an uploaded image file with caption
    """
    try:
        # Read and convert image to base64
        image_data = await image.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        result = await get_image_attribution(image_base64, caption)
        
        # Save image to cache
        img = Image.open(BytesIO(image_data))
        image_id = hash(image_base64) % 1000000
        image_path = f"image_cache/temp_image_{image_id}.png"
        img.save(image_path)
        
        return analyze_pos({
            "caption": result.caption,
            "tokens": result.tokens,
            "attributions": result.attributions,
            "image_url": f"/image/{image_id}"
        })
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to process image file: {str(e)}"
        )


@app.get("/image/{image_id}")
def get_image(image_id: int):
    """
    Serve cached image by ID
    """
    image_path = f"image_cache/temp_image_{image_id}.png"
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(image_path, media_type="image/png")


# =============================================================================
# HEALTH CHECK
# =============================================================================

@app.get("/api/health")
async def health_check():
    """
    Health check endpoint
    """
    # Test connection to attribution API
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{ATTRIBUTION_API_URL}/health")
            api_status = "connected" if response.status_code == 200 else "error"
    except:
        api_status = "disconnected"
    
    return {
        "status": "ok",
        "attribution_api": api_status,
        "attribution_api_url": ATTRIBUTION_API_URL
    }


@app.get("/")
async def root():
    """
    Root endpoint with API information
    """
    return {
        "name": "Attribution Analysis API",
        "version": "2.0.0",
        "endpoints": {
            "text_attribution": "/api/attribution",
            "word_merge": "/api/merge-words",
            "word_combinations": "/api/merge-word-combinations",
            "pos_analysis": "/api/pos",
            "pos_combinations": "/api/pos-combinations",
            "image_attribution": "/api/image-attribution",
            "image_file_upload": "/api/image-attribution-file",
            "health": "/api/health"
        }
    }