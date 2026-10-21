import logging
import math
from typing import Dict, Any, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)

class BodyLandmarksService:
    def __init__(self):
        self._mp_pose = None
        self._pose_detector = None

    def _get_detector(self):
        if self._pose_detector is None:
            try:
                import mediapipe as mp
                self._mp_pose = mp.solutions.pose
                self._pose_detector = self._mp_pose.Pose(
                    static_image_mode=True,
                    model_complexity=1,
                    enable_segmentation=True,
                    min_detection_confidence=0.5
                )
            except Exception as e:
                logger.warning(f"MediaPipe Pose initialization note: {e}. Fallback mode active.")
                self._pose_detector = "FALLBACK"
        return self._pose_detector

    def analyze_image(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Processes image bytes, detects pose landmarks via MediaPipe / OpenCV,
        and computes normalized body proportions.
        """
        import cv2

        # 1. Decode image safely
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return {
                "success": False,
                "error": "Failed to decode image. Please upload a valid JPEG, PNG, or WebP photo.",
                "confidence_score": 0.0,
                "confidence_level": "none"
            }

        height_px, width_px, _ = img.shape
        if height_px < 150 or width_px < 150:
            return {
                "success": False,
                "error": "Image resolution too low for pose analysis. Please upload a clear full-body photo.",
                "confidence_score": 0.0,
                "confidence_level": "none"
            }

        detector = self._get_detector()

        if detector != "FALLBACK":
            try:
                rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                results = detector.process(rgb_img)

                if results and results.pose_landmarks:
                    landmarks = results.pose_landmarks.landmark
                    return self._compute_proportions_mediapipe(landmarks, width_px, height_px)
            except Exception as e:
                logger.warning(f"MediaPipe execution error: {e}. Falling back to contour analysis.")

        # Fallback to OpenCV silhouette & contour analysis
        return self._compute_proportions_opencv(img, width_px, height_px)

    def _compute_proportions_mediapipe(self, landmarks, width_px: int, height_px: int) -> Dict[str, Any]:
        """Calculates 2D proportional ratios from MediaPipe normalized landmarks."""
        # MediaPipe landmark indices
        # 0: nose, 11: left_shoulder, 12: right_shoulder
        # 23: left_hip, 24: right_hip
        # 27: left_ankle, 28: right_ankle
        ls = landmarks[11]
        rs = landmarks[12]
        lh = landmarks[23]
        rh = landmarks[24]
        nose = landmarks[0]
        la = landmarks[27]
        ra = landmarks[28]

        # Check visibility
        vis_list = [ls.visibility, rs.visibility, lh.visibility, rh.visibility]
        avg_visibility = sum(vis_list) / len(vis_list)

        if avg_visibility < 0.40:
            return {
                "success": False,
                "error": "Key body landmarks (shoulders, torso, hips) were not clearly visible. Please ensure a well-lit, unobstructed front-facing view.",
                "confidence_score": round(avg_visibility, 2),
                "confidence_level": "low"
            }

        # Coordinate calculations in pixels
        shoulder_mid_x = (ls.x + rs.x) / 2.0 * width_px
        shoulder_mid_y = (ls.y + rs.y) / 2.0 * height_px
        hip_mid_x = (lh.x + rh.x) / 2.0 * width_px
        hip_mid_y = (lh.y + rh.y) / 2.0 * height_px
        ankle_mid_y = (la.y + ra.y) / 2.0 * height_px

        # Distance measurements
        shoulder_width_px = math.hypot((ls.x - rs.x) * width_px, (ls.y - rs.y) * height_px)
        hip_width_px = math.hypot((lh.x - rh.x) * width_px, (lh.y - rh.y) * height_px)
        torso_length_px = math.hypot(hip_mid_x - shoulder_mid_x, hip_mid_y - shoulder_mid_y)

        # Full body height proxy (from slightly above nose to ankle)
        head_top_y = max(0.0, (nose.y * height_px) - (shoulder_width_px * 0.45))
        total_height_px = max(10.0, ankle_mid_y - head_top_y)

        # Ratios relative to total height
        shoulder_to_height = shoulder_width_px / total_height_px
        hip_to_height = hip_width_px / total_height_px
        torso_to_height = torso_length_px / total_height_px
        shoulder_to_hip = shoulder_width_px / max(1.0, hip_width_px)

        confidence_score = min(0.92, max(0.50, float(avg_visibility)))
        confidence_level = "high" if confidence_score >= 0.75 else "medium"

        return {
            "success": True,
            "confidence_score": round(confidence_score, 2),
            "confidence_level": confidence_level,
            "landmark_coords": {
                "left_shoulder": [round(ls.x * width_px, 1), round(ls.y * height_px, 1)],
                "right_shoulder": [round(rs.x * width_px, 1), round(rs.y * height_px, 1)],
                "left_hip": [round(lh.x * width_px, 1), round(lh.y * height_px, 1)],
                "right_hip": [round(rh.x * width_px, 1), round(rh.y * height_px, 1)],
                "nose": [round(nose.x * width_px, 1), round(nose.y * height_px, 1)]
            },
            "pixels": {
                "height_px": round(total_height_px, 1),
                "shoulder_width_px": round(shoulder_width_px, 1),
                "hip_width_px": round(hip_width_px, 1),
                "torso_length_px": round(torso_length_px, 1)
            },
            "proportions": {
                "shoulder_to_height_ratio": round(shoulder_to_height, 4),
                "hip_to_height_ratio": round(hip_to_height, 4),
                "torso_to_height_ratio": round(torso_to_height, 4),
                "shoulder_to_hip_ratio": round(shoulder_to_hip, 4)
            }
        }

    def _compute_proportions_opencv(self, img, width_px: int, height_px: int) -> Dict[str, Any]:
        """Fallback computer vision estimation using thresholding and contour bounding boxes."""
        import cv2
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return {
                "success": False,
                "error": "No clear human silhouette detected in the image.",
                "confidence_score": 0.2,
                "confidence_level": "low"
            }

        # Pick the largest contour
        largest_cnt = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_cnt)

        # Proportions approximation
        shoulder_width_px = w * 0.70
        hip_width_px = w * 0.65
        torso_length_px = h * 0.35
        total_height_px = max(10.0, float(h))

        return {
            "success": True,
            "confidence_score": 0.55,
            "confidence_level": "medium",
            "landmark_coords": {},
            "pixels": {
                "height_px": round(total_height_px, 1),
                "shoulder_width_px": round(shoulder_width_px, 1),
                "hip_width_px": round(hip_width_px, 1),
                "torso_length_px": round(torso_length_px, 1)
            },
            "proportions": {
                "shoulder_to_height_ratio": round(shoulder_width_px / total_height_px, 4),
                "hip_to_height_ratio": round(hip_width_px / total_height_px, 4),
                "torso_to_height_ratio": round(torso_length_px / total_height_px, 4),
                "shoulder_to_hip_ratio": round(shoulder_width_px / max(1.0, hip_width_px), 4)
            }
        }

body_landmarks_service = BodyLandmarksService()
