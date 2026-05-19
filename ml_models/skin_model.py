import os
import cv2
import numpy as np
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import mediapipe as mp

# ==============================
# FACE DETECTOR
# ==============================
mp_face = mp.solutions.face_detection
face_detector = mp_face.FaceDetection(
    model_selection=1,
    min_detection_confidence=0.5
)

# ==============================
# PREPROCESSING
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


def normalize_lighting(img):
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    l = cv2.GaussianBlur(l, (3, 3), 0)

    lab = cv2.merge((l, a, b))
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)


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

            x1 = max(0, int(x + bw * 0.20))
            x2 = min(w, int(x + bw * 0.80))
            y1 = max(0, int(y + bh * 0.20))
            y2 = min(h, int(y + bh * 0.80))

            face = img[y1:y2, x1:x2]

            if face.size > 100:
                return face

    except Exception as e:
        print("Face detection error:", e)

    h, w, _ = img.shape

    cx1 = int(w * 0.25)
    cx2 = int(w * 0.75)
    cy1 = int(h * 0.20)
    cy2 = int(h * 0.75)

    fallback = img[cy1:cy2, cx1:cx2]

    if fallback.size > 100:
        return fallback

    return None


# ==============================
# SKIN MASK
# ==============================
def get_skin_pixels(face):
    ycrcb = cv2.cvtColor(face, cv2.COLOR_BGR2YCrCb)

    # diperlebar untuk dark/black skin
    lower = np.array([0, 125, 70], dtype=np.uint8)
    upper = np.array([255, 180, 135], dtype=np.uint8)

    mask = cv2.inRange(ycrcb, lower, upper)

    kernel = np.ones((3, 3), np.uint8)

    mask = cv2.erode(mask, kernel, iterations=1)
    mask = cv2.dilate(mask, kernel, iterations=1)

    skin_pixels = face[mask > 0]

    if len(skin_pixels) < 100:
        h, w, _ = face.shape

        # upper face fallback
        x1 = int(w * 0.30)
        x2 = int(w * 0.70)
        y1 = int(h * 0.18)
        y2 = int(h * 0.50)

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
# LABEL
# ==============================
def classify_fitzpatrick(L):
    if L >= 150:
        return "white"
    elif L >= 128:
        return "olive"
    elif L >= 105:
        return "brown"
    elif L >= 70:
        return "dark_brown"
    else:
        return "black"


# ==============================
# LOAD DATASET
# ==============================
def load_dataset(folder):
    X, y = [], []

    csv_path = os.path.join(os.path.dirname(folder), "labels.csv")
    df = pd.read_csv(csv_path)

    df["skin_tone"] = df["skin_tone"].replace({
        "dark brown": "dark_brown"
    })

    total = len(df)
    success = 0
    skipped = 0

    for _, row in df.iterrows():
        path = os.path.join(os.path.dirname(folder), row["file"])
        label = row["skin_tone"]

        img = cv2.imread(path)

        if img is None:
            skipped += 1
            continue

        img = cv2.resize(img, (300, 300))

        feat = extract_features(img)

        if feat is None:
            skipped += 1
            continue

        X.append(feat)
        y.append(label)
        success += 1

    print(f"Total dataset : {total}")
    print(f"Used images   : {success}")
    print(f"Skipped       : {skipped}")

    return np.array(X), np.array(y)


# ==============================
# TRAIN MODEL
# ==============================
def train():
    folder = "dataset/balanced_dataset/images"

    print("Loading dataset...")
    X, y = load_dataset(folder)

    if len(X) == 0:
        print("ERROR: No valid training data found.")
        return

    print("Training model...")

    model = RandomForestClassifier(
        n_estimators=900,
        max_depth=28,
        min_samples_leaf=2,
        random_state=42,
        class_weight={
            "black": 2.0,
            "dark_brown": 1.0,
            "brown": 1.0,
            "olive": 1.0,
            "white": 1.0
        }
    )

    model.fit(X, y)

    os.makedirs("ml_models", exist_ok=True)
    joblib.dump(model, "ml_models/skin_model.pkl")

    print("✅ skin_model.pkl saved successfully")


if __name__ == "__main__":
    train()