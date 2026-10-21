import math
import sqlite3
import logging
from typing import Dict, Any, List, Optional, Tuple
from app.database import get_connection
from app.models import SizeEstimateResponse

logger = logging.getLogger(__name__)

DISCLAIMER_TEXT = (
    "Note: Visual landmarks from a single 2D photograph provide an approximate proportion estimate. "
    "They do not replace physical tape measurements. Fit may vary depending on posture, clothing ease, "
    "and personal drape preferences. You can always override this recommendation manually."
)

class SizeEstimationService:
    def __init__(self, db_path=None):
        self.db_path = db_path

    def estimate_size(
        self,
        analysis_result: Dict[str, Any],
        height_cm: Optional[float] = None,
        brand: str = "Linen Trail",
        category: str = "Shirts",
        gender: str = "Men"
    ) -> SizeEstimateResponse:
        """
        Translates proportional landmarks and optional height into brand-calibrated size suggestions.
        """
        if not analysis_result.get("success"):
            return SizeEstimateResponse(
                success=False,
                confidence_level="low",
                confidence_score=0.0,
                recommended_size="M",
                alternative_sizes=["S", "L"],
                estimated_measurements_cm={},
                proportions={},
                brand_used=brand,
                category_used=category,
                calibration_method="Failed landmark detection",
                notes=[analysis_result.get("error", "Unable to detect body landmarks reliably.")],
                disclaimer=DISCLAIMER_TEXT
            )

        pixels = analysis_result.get("pixels", {})
        proportions = analysis_result.get("proportions", {})
        base_confidence = analysis_result.get("confidence_score", 0.6)

        notes = []
        is_calibrated = False

        if height_cm and height_cm >= 100 and height_cm <= 230:
            scale_cm_per_px = height_cm / max(1.0, pixels.get("height_px", 500.0))
            calibration_method = f"Calibrated using user-supplied height ({height_cm:.0f} cm)"
            is_calibrated = True
            confidence_score = min(0.92, base_confidence + 0.15)
            notes.append(f"Height calibration applied: {height_cm:.0f} cm.")
        else:
            # Baseline estimation assuming standard 170cm height
            assumed_height = 172.0 if gender.lower() == "men" else 162.0
            scale_cm_per_px = assumed_height / max(1.0, pixels.get("height_px", 500.0))
            calibration_method = f"Uncalibrated (assumed standard baseline {assumed_height:.0f} cm)"
            confidence_score = min(0.60, base_confidence)
            notes.append("Uncalibrated estimate: entering your exact height will significantly increase size accuracy.")

        # Anthropometric ellipse approximation:
        # projected 2D width 'W' corresponds to major axis 2*a = W.
        # depth ratio 'b/a' for human torso is approximately 0.72.
        # Ramanujan's perimeter approximation: P ≈ π * [ 3*(a+b) - sqrt((3a+b)*(a+3b)) ]
        shoulder_px = pixels.get("shoulder_width_px", 120.0)
        hip_px = pixels.get("hip_width_px", 110.0)

        chest_width_cm = (shoulder_px * 0.90) * scale_cm_per_px
        waist_width_cm = (hip_px * 0.82) * scale_cm_per_px
        hip_width_cm = (hip_px * 1.02) * scale_cm_per_px

        def ellipse_circ(major_width: float, depth_ratio: float = 0.72) -> float:
            a = major_width / 2.0
            b = a * depth_ratio
            return round(math.pi * (3 * (a + b) - math.sqrt((3 * a + b) * (a + 3 * b))), 1)

        est_chest = ellipse_circ(chest_width_cm, 0.75)
        est_waist = ellipse_circ(waist_width_cm, 0.70)
        est_hip = ellipse_circ(hip_width_cm, 0.74)

        estimated_measurements = {
            "chest_cm": est_chest,
            "waist_cm": est_waist,
            "hip_cm": est_hip
        }

        # Match with Brand Size Chart in SQLite
        size_chart_rows = self._get_size_chart(brand, category, gender)
        if not size_chart_rows:
            # Fallback to any brand chart for this category
            size_chart_rows = self._get_size_chart(None, category, gender)

        recommended_size, alt_sizes, match_notes = self._match_size_chart(
            estimated_measurements,
            size_chart_rows,
            category
        )
        notes.extend(match_notes)

        confidence_level = "high" if confidence_score >= 0.80 else ("medium" if confidence_score >= 0.60 else "low")
        if not is_calibrated:
            confidence_level = "uncalibrated"

        return SizeEstimateResponse(
            success=True,
            confidence_level=confidence_level,
            confidence_score=round(confidence_score, 2),
            recommended_size=recommended_size,
            alternative_sizes=alt_sizes,
            estimated_measurements_cm=estimated_measurements,
            proportions=proportions,
            brand_used=brand,
            category_used=category,
            brand_size_chart=size_chart_rows,
            calibration_method=calibration_method,
            notes=notes,
            disclaimer=DISCLAIMER_TEXT
        )

    def _get_size_chart(self, brand: Optional[str], category: str, gender: str) -> List[Dict[str, Any]]:
        conn = get_connection(self.db_path)
        try:
            if brand:
                rows = conn.execute(
                    "SELECT * FROM size_charts WHERE brand = ? AND category = ? AND gender = ? ORDER BY id ASC",
                    (brand, category, gender)
                ).fetchall()
                if rows:
                    return [dict(r) for r in rows]

            # Try category & gender without brand constraint
            rows = conn.execute(
                "SELECT * FROM size_charts WHERE category = ? AND gender = ? ORDER BY id ASC",
                (category, gender)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def _match_size_chart(
        self,
        measurements: Dict[str, float],
        chart: List[Dict[str, Any]],
        category: str
    ) -> Tuple[str, List[str], List[str]]:
        if not chart:
            return "M", ["S", "L"], ["Standard size chart unavailable; defaulting to medium."]

        is_bottom = category.lower() in ["trousers", "pants", "shorts", "skirts"]
        target_val = measurements["waist_cm"] if is_bottom else measurements["chest_cm"]
        target_key = "waist" if is_bottom else "chest"

        scored_sizes = []
        for row in chart:
            min_val = row[f"{target_key}_min_cm"]
            max_val = row[f"{target_key}_max_cm"]
            mid_val = (min_val + max_val) / 2.0
            diff = abs(target_val - mid_val)

            # Check boundary overlap
            in_range = (target_val >= min_val and target_val <= max_val)
            scored_sizes.append({
                "label": row["size_label"],
                "in_range": in_range,
                "diff": diff,
                "range": f"{min_val:.0f}-{max_val:.0f} cm",
                "garment": row.get(f"garment_{target_key}_cm", 0.0)
            })

        # Sort by distance
        scored_sizes.sort(key=lambda s: s["diff"])
        best = scored_sizes[0]["label"]

        alts = [s["label"] for s in scored_sizes[1:3]]
        notes = []

        if scored_sizes[0]["in_range"]:
            notes.append(f"Estimated {target_key} ({target_val:.1f} cm) fits comfortably within {best} range ({scored_sizes[0]['range']}).")
        else:
            notes.append(f"Estimated {target_key} ({target_val:.1f} cm) is closest to size {best} ({scored_sizes[0]['range']}).")

        # Boundary note if near adjacent size
        if len(scored_sizes) > 1 and scored_sizes[1]["diff"] - scored_sizes[0]["diff"] < 3.0:
            notes.append(f"Borderline fit: consider {scored_sizes[1]['label']} if you prefer extra ease.")

        return best, alts, notes

size_estimation_service = SizeEstimationService()
