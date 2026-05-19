from flask import Blueprint, request, jsonify
import os

from detectors.skin_detector import detect_skin_tone   # 🔥 AI ML
from utils.recommender import recommend                # filtering

tryon_bp = Blueprint("tryon", __name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@tryon_bp.route("/tryon", methods=["POST"])
def tryon():
    try:
        # ==============================
        # VALIDASI FILE
        # ==============================
        if "image" not in request.files:
            return jsonify({"error": "No image uploaded"}), 400

        file = request.files["image"]

        if file.filename == "":
            return jsonify({"error": "Empty filename"}), 400

        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        print("✔ File disimpan:", filepath)

        # ==============================
        # PARAMETER TAMBAHAN
        # ==============================
        gender = request.form.get("gender", "female")
        size = request.form.get("size", None)

        # ==============================
        # 🔥 AI - SKIN DETECTION
        # ==============================
        skin_tone = detect_skin_tone(filepath)   # ML + CV + Image Processing

        if skin_tone == "unknown":
            skin_tone = None

        # ==============================
        # BODY SHAPE (MANUAL)
        # ==============================
        body_shape = request.form.get("body_shape", "hourglass")

        # ==============================
        # RECOMMENDER
        # ==============================
        recommendations = recommend(
            skin_tone=skin_tone,
            body_shape=body_shape,
            size_estimate=size,
            gender=gender
        )

        return jsonify({
            "status": "success",
            "skin_tone": skin_tone,
            "body_shape": body_shape,
            "recommendations": recommendations
        })

    except Exception as e:
        print("❌ ERROR TRYON:", str(e))
        return jsonify({"error": str(e)}), 500