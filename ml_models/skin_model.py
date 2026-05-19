import os
import cv2
import numpy as np
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

# ==============================
# FACE DETECTOR (TETAP ADA)
# ==============================
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
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
# FEATURE EXTRACTION (UPGRADE)
# ==============================
def extract_features(img):
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)

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
# LABEL (DIBIARKAN AGAR STRUKTUR TETAP)
# ==============================
def classify_fitzpatrick(L):
    if L >= 138:
        return "white"
    elif L >= 122:
        return "olive"
    elif L >= 110:
        return "brown"
    elif L >= 97:
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

    for _, row in df.iterrows():
        path = os.path.join(os.path.dirname(folder), row["file"])
        label = row["skin_tone"]

        img = cv2.imread(path)
        if img is None:
            continue

        img = cv2.resize(img, (200, 200))
        img = gray_world(img)

        feat = extract_features(img)

        X.append(feat)
        y.append(label)

    return np.array(X), np.array(y)


# ==============================
# TRAIN MODEL
# ==============================
def train():
    folder = "dataset/balanced_dataset/images"

    print("Loading dataset...")
    X, y = load_dataset(folder)

    print("Training model...")

    model = RandomForestClassifier(
        n_estimators=500,
        max_depth=25,
        random_state=42,
        class_weight="balanced"
    )

    model.fit(X, y)

    os.makedirs("ml_models", exist_ok=True)
    joblib.dump(model, "ml_models/skin_model.pkl")

    print("✅ Model saved")


if __name__ == "__main__":
    train()