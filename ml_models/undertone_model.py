import os
import cv2
import numpy as np
import pandas as pd
import joblib

from sklearn.ensemble import RandomForestClassifier
from collections import Counter

# ==============================
# CONFIG
# ==============================
BASE = "dataset/balanced_dataset"

# 🔥 FIX DATASET PATH
TRAIN_CSV = os.path.join(BASE, "labels.csv")

# 🔥 IMAGE FOLDER
IMAGE_DIR = os.path.join(BASE, "images")


# ==============================
# FEATURE EXTRACTION (A & B LAB)
# ==============================
def extract_AB(img_path):

    img = cv2.imread(img_path)

    if img is None:
        print("❌ Failed:", img_path)
        return None

    try:
        img = cv2.resize(img, (100, 100))

        lab = cv2.cvtColor(
            img,
            cv2.COLOR_BGR2LAB
        )

        A = np.median(lab[:, :, 1])
        B = np.median(lab[:, :, 2])

        return A, B

    except Exception as e:
        print("❌ EXTRACT ERROR:", e)
        return None


# ==============================
# LOAD DATASET
# ==============================
def load_dataset():

    # 🔥 FIX CSV
    df = pd.read_csv(TRAIN_CSV)

    ratios = []
    data = []

    print("🔄 Extracting features...")
    print("TOTAL:", len(df))

    for i, row in df.iterrows():

        try:

            # 🔥 FIX FILE PATH
            img_path = os.path.join(
                BASE,
                row["file"]
            )

            result = extract_AB(img_path)

            if result is None:
                continue

            A, B = result

            # 🔥 UNDERTONE RATIO
            ratio = (
                (B - A) /
                (abs(A) + abs(B) + 1e-6)
            )

            ratios.append(ratio)

            data.append((A, B))

            # DEBUG
            if i % 1000 == 0:
                print(f"Processed {i}")

        except Exception as e:
            print("❌ LOAD ERROR:", e)

    print("✅ SUCCESS LOAD:", len(data))

    return data, ratios


# ==============================
# BUILD LABEL (BALANCED)
# ==============================
def build_labels(data, ratios):

    print("📊 Calculating thresholds...")

    low, high = np.percentile(
        ratios,
        [33, 66]
    )

    print(f"LOW  threshold: {low:.4f}")
    print(f"HIGH threshold: {high:.4f}")

    X = []
    y = []

    for (A, B), ratio in zip(data, ratios):

        # 🔥 WARM
        if ratio > high:
            label = "warm"

        # 🔥 COOL
        elif ratio < low:
            label = "cool"

        # 🔥 NEUTRAL
        else:
            label = "neutral"

        X.append([A, B])
        y.append(label)

    print(
        "📊 Label distribution:",
        Counter(y)
    )

    return np.array(X), np.array(y)


# ==============================
# TRAIN MODEL
# ==============================
def train_model(X, y):

    print("🤖 Training model...")

    model = RandomForestClassifier(
        n_estimators=150,
        max_depth=10,
        class_weight="balanced",
        random_state=42
    )

    model.fit(X, y)

    print("✅ Training finished")

    return model


# ==============================
# SAVE MODEL
# ==============================
def save_model(model):

    os.makedirs(
        "ml_models",
        exist_ok=True
    )

    path = "ml_models/undertone_model.pkl"

    joblib.dump(model, path)

    print(f"✅ Model saved at {path}")


# ==============================
# MAIN
# ==============================
def main():

    data, ratios = load_dataset()

    if len(data) == 0:
        print("❌ No valid data found")
        return

    X, y = build_labels(
        data,
        ratios
    )

    model = train_model(X, y)

    save_model(model)

    print("🎉 DONE")


if __name__ == "__main__":
    main()