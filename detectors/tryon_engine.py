import cv2                      # Computer Vision
import mediapipe as mp          # 🔥 AI Pose Detection
import numpy as np

# =========================
# INIT MODEL (AI)
# =========================
mp_pose = mp.solutions.pose
mp_selfie = mp.solutions.selfie_segmentation

_pose = mp_pose.Pose(
    static_image_mode=True,
    model_complexity=1,
    enable_segmentation=False
)
# 🔥 AI: Mediapipe Pose (deteksi tubuh)

_segment = mp_selfie.SelfieSegmentation(model_selection=1)
# 🔥 AI: segmentasi tubuh


# =========================
# MAIN FUNCTION
# =========================
def virtual_try_on(body_img_path, cloth_img_path, output_path):
    print("=== TRYON STABLE V2 ===")

    body = cv2.imread(body_img_path)
    cloth = cv2.imread(cloth_img_path, cv2.IMREAD_UNCHANGED)

    if body is None:
        return False

    if cloth is None:
        return False

    if cloth.shape[2] != 4:
        return False

    h, w = body.shape[:2]

    rgb = cv2.cvtColor(body, cv2.COLOR_BGR2RGB)

    # =========================
    # 🔥 AI POSE DETECTION
    # =========================
    pose = _pose.process(rgb)

    if not pose.pose_landmarks:
        return fallback_tryon(body, cloth, output_path)

    lm = pose.pose_landmarks.landmark

    def pt(p):
        return int(p.x * w), int(p.y * h)

    # 🔥 landmark tubuh
    ls = pt(lm[mp_pose.PoseLandmark.LEFT_SHOULDER])
    rs = pt(lm[mp_pose.PoseLandmark.RIGHT_SHOULDER])
    lh = pt(lm[mp_pose.PoseLandmark.LEFT_HIP])
    rh = pt(lm[mp_pose.PoseLandmark.RIGHT_HIP])

    # =========================
    # SIZE ESTIMATION
    # =========================
    shoulder_width = abs(rs[0] - ls[0])
    torso_height = abs(lh[1] - ls[1])

    shoulder_width = int(np.clip(shoulder_width, 140, w * 0.5))
    torso_height = int(np.clip(torso_height, 180, h * 0.6))

    # =========================
    # RESIZE BAJU
    # =========================
    cloth = cv2.resize(
        cloth,
        (int(shoulder_width * 1.2), int(torso_height * 1.1))
    )

    h_c, w_c = cloth.shape[:2]

    cloth_rgb = cloth[:, :, :3]
    alpha = cloth[:, :, 3] / 255.0

    # =========================
    # POSISI BAJU
    # =========================
    center_x = int((ls[0] + rs[0]) / 2)
    chest_y = int((ls[1] + lh[1]) / 2)

    x = int(center_x - w_c / 2)
    y = int(chest_y - h_c * 0.35)

    x1 = max(0, x)
    y1 = max(0, y)
    x2 = min(w, x + w_c)
    y2 = min(h, y + h_c)

    cloth_crop = cloth[
        (y1 - y):(y2 - y),
        (x1 - x):(x2 - x)
    ]

    cloth_rgb = cloth_crop[:, :, :3]
    alpha = cloth_crop[:, :, 3] / 255.0

    # =========================
    # 🔥 AI SEGMENTATION
    # =========================
    seg = _segment.process(rgb).segmentation_mask
    body_mask = (seg > 0.5).astype(np.float32)

    mask_region = body_mask[y1:y2, x1:x2]

    # =========================
    # SHADING (REALISM)
    # =========================
    gray = cv2.cvtColor(body, cv2.COLOR_BGR2GRAY)
    shade = cv2.GaussianBlur(gray, (31, 31), 0) / 255.0
    shade = shade[y1:y2, x1:x2]

    cloth_rgb = cloth_rgb * (0.75 + 0.25 * shade[..., None])
    cloth_rgb = np.clip(cloth_rgb, 0, 255).astype(np.uint8)

    # =========================
    # SMOOTH EDGE
    # =========================
    alpha = cv2.GaussianBlur(alpha, (7, 7), 0)
    alpha = alpha * (1 - mask_region * 0.5)
    alpha = alpha[..., None]

    # =========================
    # BLENDING
    # =========================
    body_region = body[y1:y2, x1:x2]

    result_region = (
        alpha * cloth_rgb +
        (1 - alpha) * body_region
    ).astype(np.uint8)

    result = body.copy()
    result[y1:y2, x1:x2] = result_region

    cv2.imwrite(output_path, result)

    return True