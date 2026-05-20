import cv2
import numpy as np
import joblib
import mediapipe as mp

# ==============================
# LOAD MODEL
# ==============================
try:
    model = joblib.load("ml_models/skin_model.pkl")
except:
    model = None

try:
    undertone_model = joblib.load("ml_models/undertone_model.pkl")
except:
    undertone_model = None


# ==============================
# MEDIAPIPE
# ==============================
mp_face = mp.solutions.face_detection
face_detector = mp_face.FaceDetection(
    model_selection=1,
    min_detection_confidence=0.5
)


# ==============================
# PREPROCESS
# ==============================
def gray_world(img):
    result = img.astype(np.float32)

    avg_b = np.mean(result[:, :, 0])
    avg_g = np.mean(result[:, :, 1])
    avg_r = np.mean(result[:, :, 2])

    avg_gray = (avg_b + avg_g + avg_r) / 3

    result[:, :, 0] *= (avg_gray / (avg_b + 1e-6))
    result[:, :, 1] *= (avg_gray / (avg_g + 1e-6))
    result[:, :, 2] *= (avg_gray / (avg_r + 1e-6))

    return np.clip(result, 0, 255).astype(np.uint8)


# ==============================
# FACE DETECTION
# ==============================
def detect_face(img):
    try:
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        result = face_detector.process(rgb)

        if result.detections:
            bbox = result.detections[0].location_data.relative_bounding_box

            h, w, _ = img.shape

            x = int(bbox.xmin * w)
            y = int(bbox.ymin * h)
            bw = int(bbox.width * w)
            bh = int(bbox.height * h)

            x1 = max(0, int(x + bw * 0.18))
            x2 = min(w, int(x + bw * 0.82))
            y1 = max(0, int(y + bh * 0.12))
            y2 = min(h, int(y + bh * 0.72))

            face = img[y1:y2, x1:x2]

            if face.size > 100:
                return face

    except Exception as e:
        print("Face error:", e)

    h, w, _ = img.shape

    cx1 = int(w * 0.25)
    cx2 = int(w * 0.75)
    cy1 = int(h * 0.12)
    cy2 = int(h * 0.60)

    fallback = img[cy1:cy2, cx1:cx2]

    if fallback.size > 100:
        return fallback

    return None


# ==============================
# SKIN MASK
# ==============================
def get_skin_pixels(face):
    ycrcb = cv2.cvtColor(face, cv2.COLOR_BGR2YCrCb)
    lab = cv2.cvtColor(face, cv2.COLOR_BGR2LAB)

    lower_ycrcb = np.array([0, 120, 70], dtype=np.uint8)
    upper_ycrcb = np.array([255, 185, 145], dtype=np.uint8)

    mask1 = cv2.inRange(ycrcb, lower_ycrcb, upper_ycrcb)

    A = lab[:, :, 1]
    B = lab[:, :, 2]

    mask2 = ((A > 118) & (A < 175) & (B > 110) & (B < 185)).astype(np.uint8) * 255

    mask = cv2.bitwise_or(mask1, mask2)

    kernel = np.ones((3, 3), np.uint8)

    mask = cv2.erode(mask, kernel, iterations=1)
    mask = cv2.dilate(mask, kernel, iterations=2)
    mask = cv2.medianBlur(mask, 3)

    skin_pixels = face[mask > 0]

    if len(skin_pixels) > 0:
        brightness = np.mean(skin_pixels, axis=1)
        skin_pixels = skin_pixels[brightness > 35]

    if len(skin_pixels) < 100:
        h, w, _ = face.shape

        x1 = int(w * 0.25)
        x2 = int(w * 0.75)
        y1 = int(h * 0.10)
        y2 = int(h * 0.45)

        center = face[y1:y2, x1:x2]

        return center.reshape(-1, 3)

    return skin_pixels


# ==============================
# FEATURE EXTRACTION
# ==============================
def extract_features(img):
    face = detect_face(img)

    if face is None or face.size == 0:
        return None

    skin_pixels = get_skin_pixels(face)

    if skin_pixels is None or len(skin_pixels) == 0:
        return None

    lab = cv2.cvtColor(
        skin_pixels.reshape(-1, 1, 3),
        cv2.COLOR_BGR2LAB
    )

    L_channel = lab[:, :, 0].flatten()
    A_channel = lab[:, :, 1].flatten()
    B_channel = lab[:, :, 2].flatten()

    features = [
        np.mean(L_channel),
        np.std(L_channel),
        np.percentile(L_channel, 10),

        np.mean(A_channel),
        np.std(A_channel),
        np.median(A_channel),

        np.mean(B_channel),
        np.std(B_channel),
        np.median(B_channel),
    ]

    return features


# ==============================
# UNDERTONE
# ==============================
def detect_undertone(features):
    A = features[5]
    B = features[8]

    if undertone_model:
        try:
            return undertone_model.predict([[A, B]])[0]
        except:
            pass

    ratio = (B - A) / (abs(A) + abs(B) + 1e-6)

    if ratio > 0.02:
        return "warm"
    elif ratio < -0.02:
        return "cool"
    else:
        return "neutral"


# ==============================
# MAIN
# ==============================
def detect_skin_tone(image_path):
    img = cv2.imread(image_path)

    if img is None:
        return {
            "tone": "unknown",
            "undertone": "unknown"
        }

    img = cv2.resize(img, (300, 300))

    feat = extract_features(img)

    if feat is None:
        return {
            "tone": "unknown",
            "undertone": "unknown"
        }

    if model:
        try:
            tone = model.predict([feat])[0]
        except:
            tone = "unknown"
    else:
        tone = "unknown"

    undertone = detect_undertone(feat)

    return {
        "tone": tone,
        "undertone": undertone
    }