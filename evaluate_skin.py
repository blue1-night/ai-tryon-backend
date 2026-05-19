import os
import cv2
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score
from sklearn.metrics import f1_score
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix

from detectors.skin_detector import extract_features

DATASET_PATH = r"dataset/balanced_dataset"

df = pd.read_csv(os.path.join(DATASET_PATH, "labels.csv"))

# normalisasi label
df["skin_tone"] = df["skin_tone"].replace({
    "dark brown": "dark_brown"
})

X = []
y = []

print("Extracting features...")

for _, row in df.iterrows():
    img_path = os.path.join(DATASET_PATH, row["file"])
    label = row["skin_tone"]

    if not os.path.exists(img_path):
        continue

    img = cv2.imread(img_path)

    if img is None:
        continue

    img = cv2.resize(img, (300, 300))

    feat = extract_features(img)

    if feat is None:
        continue

    X.append(feat)
    y.append(label)

X = np.array(X)
y = np.array(y)

print("Total valid samples:", len(X))

# ==========================
# TRAIN TEST SPLIT
# ==========================
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

print("Train samples:", len(X_train))
print("Test samples :", len(X_test))

# ==========================
# TRAIN MODEL
# ==========================
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

print("Training model...")
model.fit(X_train, y_train)

# ==========================
# PREDICT
# ==========================
y_pred = model.predict(X_test)

# ==========================
# EVALUATION
# ==========================
acc = accuracy_score(y_test, y_pred)
prec = precision_score(y_test, y_pred, average="weighted")
rec = recall_score(y_test, y_pred, average="weighted")
f1 = f1_score(y_test, y_pred, average="weighted")

print("\n===== HASIL =====")
print("Accuracy :", acc)
print("Precision:", prec)
print("Recall   :", rec)
print("F1 Score :", f1)

print("\n===== REPORT =====")
print(classification_report(y_test, y_pred))

print("\n===== CONFUSION MATRIX =====")
print(confusion_matrix(y_test, y_pred))