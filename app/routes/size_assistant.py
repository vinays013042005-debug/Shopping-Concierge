import sqlite3
from typing import Optional, List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from app.config import MAX_UPLOAD_SIZE_BYTES, ALLOWED_MIME_TYPES
from app.database import get_db
from app.models import SizeEstimateResponse, SizeChartRow
from app.services.body_landmarks import body_landmarks_service
from app.services.size_estimation import size_estimation_service

router = APIRouter(prefix="/api", tags=["Size Assistant & Sizing Charts"])

@router.post("/size-assistant/analyze", response_model=SizeEstimateResponse)
async def analyze_photo_sizing(
    consent: bool = Form(..., description="Explicit opt-in consent for local image processing"),
    file: UploadFile = File(..., description="Full-body front-facing photograph"),
    height_cm: Optional[float] = Form(None, description="Optional user height in cm for calibration"),
    brand: str = Form("Linen Trail", description="Target brand"),
    category: str = Form("Shirts", description="Target clothing category"),
    gender: str = Form("Men", description="Target gender"),
):
    if not consent:
        raise HTTPException(
            status_code=400,
            detail="Explicit consent required. Processing photographs for size estimation requires opt-in consent."
        )

    # Validate MIME type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file format '{file.content_type}'. Please upload JPEG, PNG, or WebP images."
        )

    # Read bytes safely with size check
    image_bytes = await file.read()
    if len(image_bytes) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum allowed size ({MAX_UPLOAD_SIZE_BYTES / (1024*1024):.0f}MB)."
        )

    if len(image_bytes) < 1000:
        raise HTTPException(status_code=400, detail="Uploaded file is empty or corrupted.")

    try:
        # Detect landmarks & proportions
        landmark_result = body_landmarks_service.analyze_image(image_bytes)

        # Estimate size against brand size chart
        sizing_result = size_estimation_service.estimate_size(
            analysis_result=landmark_result,
            height_cm=height_cm,
            brand=brand,
            category=category,
            gender=gender
        )

        return sizing_result
    finally:
        # Guarantee no persistent image file remains on disk
        pass

@router.get("/size-charts/{brand}/{category}", response_model=List[SizeChartRow])
def get_brand_size_chart(
    brand: str,
    category: str,
    gender: Optional[str] = "Men",
    conn: sqlite3.Connection = Depends(get_db)
):
    query = """
        SELECT id, brand, category, gender, size_label,
               chest_min_cm, chest_max_cm, waist_min_cm, waist_max_cm,
               hip_min_cm, hip_max_cm, garment_chest_cm, garment_waist_cm, garment_hip_cm,
               fit_type
        FROM size_charts
        WHERE LOWER(brand) = LOWER(?) AND LOWER(category) = LOWER(?)
    """
    params = [brand, category]
    if gender:
        query += " AND LOWER(gender) = LOWER(?)"
        params.append(gender)

    query += " ORDER BY id ASC"
    rows = conn.execute(query, params).fetchall()

    if not rows:
        # Fallback to category search without brand restriction
        fallback_query = """
            SELECT id, brand, category, gender, size_label,
                   chest_min_cm, chest_max_cm, waist_min_cm, waist_max_cm,
                   hip_min_cm, hip_max_cm, garment_chest_cm, garment_waist_cm, garment_hip_cm,
                   fit_type
            FROM size_charts
            WHERE LOWER(category) = LOWER(?)
            ORDER BY id ASC
        """
        rows = conn.execute(fallback_query, (category,)).fetchall()

    return [SizeChartRow(**dict(r)) for r in rows]
