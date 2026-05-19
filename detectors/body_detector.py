import cv2
import numpy as np
import math
import mediapipe as mp

mp_pose = mp.solutions.pose
mp_selfie = mp.solutions.selfie_segmentation


# ==============================
# HITUNG JARAK PIXEL
# ==============================
def _pixel_dist(pt1, pt2, w, h):
    x1, y1 = int(pt1.x * w), int(pt1.y * h)
    x2, y2 = int(pt2.x * w), int(pt2.y * h)

    return math.hypot(x2 - x1, y2 - y1)


# ==============================
# BODY SHAPE DETECTOR
# ==============================
def detect_body_shape_and_measurements(
    image_path,
    user_height_cm=None
):

    img = cv2.imread(image_path)

    if img is None:
        return {
            "shape": "unknown",
            "confidence": 0.0,
            "measurements": {}
        }

    h, w = img.shape[:2]

    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # ==============================
    # POSE DETECTION
    # ==============================
    with mp_pose.Pose(
        static_image_mode=True,
        model_complexity=1,
        enable_segmentation=False
    ) as pose:

        results = pose.process(rgb)

    if not results.pose_landmarks:
        return {
            "shape": "unknown",
            "confidence": 0.0,
            "measurements": {}
        }

    lm = results.pose_landmarks.landmark

    # ==============================
    # LANDMARK
    # ==============================
    l_sh = lm[mp_pose.PoseLandmark.LEFT_SHOULDER]
    r_sh = lm[mp_pose.PoseLandmark.RIGHT_SHOULDER]

    l_hip = lm[mp_pose.PoseLandmark.LEFT_HIP]
    r_hip = lm[mp_pose.PoseLandmark.RIGHT_HIP]

    # ==============================
    # SHOULDER & HIP
    # ==============================
    shoulder_px = _pixel_dist(
        l_sh,
        r_sh,
        w,
        h
    )

    hip_px = _pixel_dist(
        l_hip,
        r_hip,
        w,
        h
    )

    # ==============================
    # SELFIE SEGMENTATION
    # ==============================
    with mp_selfie.SelfieSegmentation(
        model_selection=1
    ) as segment:

        seg = segment.process(rgb).segmentation_mask

    mask = (seg > 0.5).astype(np.uint8)

    # ==============================
    # ESTIMASI PINGGANG
    # ==============================
    shoulder_y = int(
        ((l_sh.y + r_sh.y) / 2) * h
    )

    hip_y = int(
        ((l_hip.y + r_hip.y) / 2) * h
    )

    waist_y = int(
        shoulder_y + (hip_y - shoulder_y) * 0.55
    )

    waist_y = max(0, min(h - 1, waist_y))

    row = mask[waist_y]

    xs = np.where(row > 0)[0]

    if len(xs) > 10:
        waist_px = xs.max() - xs.min()
    else:
        waist_px = hip_px * 0.90

    # ==============================
    # RATIO
    # ==============================
    shoulder_hip_ratio = (
        shoulder_px / (hip_px + 1e-6)
    )

    waist_ratio = (
        waist_px / (max(shoulder_px, hip_px) + 1e-6)
    )

    ratio_diff = abs(
        shoulder_px - hip_px
    ) / (max(shoulder_px, hip_px) + 1e-6)

    # ==============================
    # BODY SHAPE RULE
    # ==============================

    # ===== APPLE =====
    if waist_ratio >= 0.92:
        shape = "apple"
        confidence = 0.84

    # ===== HOURGLASS =====
    elif (
        ratio_diff < 0.08 and
        waist_ratio < 0.72
    ):
        shape = "hourglass"
        confidence = 0.90

    # ===== INVERTED TRIANGLE =====
    elif shoulder_hip_ratio >= 1.08:
        shape = "inverted_triangle"
        confidence = 0.86

    # ===== PEAR =====
    elif shoulder_hip_ratio <= 0.92:
        shape = "pear"
        confidence = 0.86

    # ===== RECTANGLE =====
    else:
        shape = "rectangle"
        confidence = 0.88

    # ==============================
    # NORMALISASI CONFIDENCE
    # ==============================
    confidence = round(
        max(0.5, min(confidence, 0.99)),
        3
    )

    # ==============================
    # RETURN
    # ==============================
    return {
        "shape": shape,

        "confidence": confidence,

        "measurements": {

            "shoulder_px": round(
                shoulder_px,
                2
            ),

            "hip_px": round(
                hip_px,
                2
            ),

            "waist_px": round(
                waist_px,
                2
            ),

            "shoulder_ratio": round(
                shoulder_hip_ratio,
                3
            ),

            "waist_ratio": round(
                waist_ratio,
                3
            ),

            "ratio_diff": round(
                ratio_diff,
                3
            )
        }
    }