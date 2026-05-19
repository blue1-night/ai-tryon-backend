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

            x1 = max(0, int(x + bw * 0.2))
            x2 = min(w, int(x + bw * 0.8))
            y1 = max(0, int(y + bh * 0.2))
            y2 = min(h, int(y + bh * 0.8))

            face = img[y1:y2, x1:x2]

            if face.size > 100:
                return face

    except Exception as e:
        print("Face error:", e)

    return img


# ==============================
# FEATURE EXTRACTION (UPGRADE)
# ==============================
def extract_features(img):
    face = detect_face(img)

    if face is None or face.size == 0:
        return None

    lab = cv2.cvtColor(face, cv2.COLOR_BGR2LAB)

    L_channel = lab[:, :, 0].flatten()
    A_channel = lab[:, :, 1].flatten()
    B_channel = lab[:, :, 2].flatten()

    features = [
        np.mean(L_channel),
        np.std(L_channel),
        np.median(L_channel),

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

    if ratio > 0.03:
        return "warm"
    elif ratio < -0.03:
        return "cool"
    else:
        return "neutral"


# ==============================
# MAIN
# ==============================
def detect_skin_tone(image_path):
    img = cv2.imread(image_path)

    if img is None:
        return "unknown"

    img = cv2.resize(img, (300, 300))
    img = gray_world(img)

    feat = extract_features(img)

    if feat is None:
        return "unknown"

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