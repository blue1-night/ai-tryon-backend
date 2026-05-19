import os
import cv2
import pandas as pd
from sklearn.metrics import accuracy_score
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score
from sklearn.metrics import f1_score
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix

from detectors.skin_detector import detect_skin_tone

DATASET_PATH = r"dataset/balanced_dataset"

df = pd.read_csv(os.path.join(DATASET_PATH, "labels.csv"))

# normalisasi label
df["skin_tone"] = df["skin_tone"].replace({
    "dark brown": "dark_brown"
})

y_true = []
y_pred = []

for _, row in df.iterrows():
    img_path = os.path.join(DATASET_PATH, row["file"])
    true_label = row["skin_tone"]

    if not os.path.exists(img_path):
        continue

    try:
        result = detect_skin_tone(img_path)

        if isinstance(result, dict):
            pred = result["tone"]
        else:
            pred = result

        if pred == "unknown":
            continue

        y_true.append(true_label)
        y_pred.append(pred)

        print(f"TRUE: {true_label} | PRED: {pred}")

    except Exception as e:
        print("ERROR:", e)

print("\nTOTAL TESTED:", len(y_true))

acc = accuracy_score(y_true, y_pred)
prec = precision_score(y_true, y_pred, average="weighted")
rec = recall_score(y_true, y_pred, average="weighted")
f1 = f1_score(y_true, y_pred, average="weighted")

print("\n===== HASIL =====")
print("Accuracy :", acc)
print("Precision:", prec)
print("Recall   :", rec)
print("F1 Score :", f1)

print("\n===== REPORT =====")
print(classification_report(y_true, y_pred))

print("\n===== CONFUSION MATRIX =====")
print(confusion_matrix(y_true, y_pred))