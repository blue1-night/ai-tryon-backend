def body_shape_from_image(image):
    try:
        import cv2
        import mediapipe as mp
        import numpy as np

        mp_pose = mp.solutions.pose
        mp_selfie = mp.solutions.selfie_segmentation

        img = cv2.imread(image)
        if img is None:
            return None, 0.0

        h, w = img.shape[:2]
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # ===== POSE DETECTION (AI) =====
        with mp_pose.Pose(static_image_mode=True) as pose:
            result = pose.process(rgb)

        if not result.pose_landmarks:
            return None, 0.0

        lm = result.pose_landmarks.landmark

        def pt(p):
            return int(p.x * w), int(p.y * h)

        ls = pt(lm[mp_pose.PoseLandmark.LEFT_SHOULDER])
        rs = pt(lm[mp_pose.PoseLandmark.RIGHT_SHOULDER])
        lh = pt(lm[mp_pose.PoseLandmark.LEFT_HIP])
        rh = pt(lm[mp_pose.PoseLandmark.RIGHT_HIP])

        shoulder_width = abs(rs[0] - ls[0])
        hip_width = abs(rh[0] - lh[0])

        if shoulder_width == 0 or hip_width == 0:
            return None, 0.0

        # ===== SEGMENTASI (AI) =====
        with mp_selfie.SelfieSegmentation(model_selection=1) as segment:
            seg = segment.process(rgb).segmentation_mask

        mask = (seg > 0.5).astype(np.uint8)

        # ===== DETEKSI PINGGANG =====
        mid_y = int((ls[1] + lh[1]) / 2)
        row = mask[mid_y]

        xs = np.where(row > 0)[0]

        if len(xs) > 0:
            waist_width = xs.max() - xs.min()
        else:
            waist_width = hip_width * 0.9

        # ===== RATIO =====
        shoulder_ratio = shoulder_width / hip_width
        waist_ratio = waist_width / shoulder_width

        # ===== RULE =====
        if waist_ratio > 0.95:
            shape = "apple"
        elif waist_ratio < 0.65 and abs(shoulder_width - hip_width) < 40:
            shape = "hourglass"
        elif shoulder_ratio > 1.15:
            shape = "inverted_triangle"
        elif shoulder_ratio < 0.85:
            shape = "pear"
        else:
            shape = "rectangle"

        confidence = min(0.9, abs(shoulder_ratio - 1.0) + abs(waist_ratio - 0.8))

        return shape, confidence

    except Exception as e:
        print("VISUAL ERROR:", e)
        return None, 0.0