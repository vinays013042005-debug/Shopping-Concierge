import pytest
import tempfile
from pathlib import Path
from scripts.seed_database import seed_database
from app.services.size_estimation import SizeEstimationService
from app.services.body_landmarks import BodyLandmarksService

@pytest.fixture
def temp_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    seed_database(db_path)
    yield db_path
    if db_path.exists():
        try:
            db_path.unlink()
        except Exception:
            pass

def test_size_chart_matching_with_height_calibration(temp_db):
    sizing = SizeEstimationService(db_path=temp_db)
    
    mock_analysis = {
        "success": True,
        "confidence_score": 0.85,
        "pixels": {
            "height_px": 600.0,
            "shoulder_width_px": 140.0,
            "hip_width_px": 120.0,
            "torso_length_px": 210.0
        },
        "proportions": {
            "shoulder_to_height_ratio": 0.2333,
            "hip_to_height_ratio": 0.2000
        }
    }

    # Calibrated with 175 cm height
    result = sizing.estimate_size(
        analysis_result=mock_analysis,
        height_cm=175.0,
        brand="Linen Trail",
        category="Shirts",
        gender="Men"
    )

    assert result.success is True
    assert result.confidence_level in ["high", "medium"]
    assert result.recommended_size in ["S", "M", "L", "XL"]
    assert "chest_cm" in result.estimated_measurements_cm
    assert result.estimated_measurements_cm["chest_cm"] > 70.0
    assert len(result.brand_size_chart) > 0
    assert "Calibrated" in result.calibration_method

def test_uncalibrated_photo_indicates_lower_confidence(temp_db):
    sizing = SizeEstimationService(db_path=temp_db)
    
    mock_analysis = {
        "success": True,
        "confidence_score": 0.80,
        "pixels": {
            "height_px": 550.0,
            "shoulder_width_px": 130.0,
            "hip_width_px": 110.0
        },
        "proportions": {}
    }

    # No height supplied (uncalibrated)
    result = sizing.estimate_size(
        analysis_result=mock_analysis,
        height_cm=None,
        brand="Linen Trail",
        category="Shirts",
        gender="Men"
    )

    assert result.success is True
    assert result.confidence_level == "uncalibrated"
    assert any("uncalibrated" in note.lower() for note in result.notes)
    assert len(result.disclaimer) > 0

def test_low_confidence_or_corrupted_image(temp_db):
    landmarks_service = BodyLandmarksService()
    # Pass random garbage bytes
    corrupt_bytes = b"NOT_A_VALID_IMAGE_DATA_12345"
    analysis = landmarks_service.analyze_image(corrupt_bytes)
    assert analysis["success"] is False
    assert "decode" in analysis["error"].lower() or "valid" in analysis["error"].lower()

    sizing = SizeEstimationService(db_path=temp_db)
    res = sizing.estimate_size(analysis)
    assert res.success is False
    assert res.confidence_level == "low"
