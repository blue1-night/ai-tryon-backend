import os
from uuid import uuid4
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from config import Config
from models import db
from auth import auth_bp
from routes.admin_clothing import admin_clothing_bp
from utils.recommender import recommend
from utils.size_predictor import predict_size
from body_shape.fusion import detect_body_shape

app = Flask(__name__)
app.config.from_object(Config)

CORS(app)

db.init_app(app)
jwt = JWTManager(app)

app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(admin_clothing_bp)

with app.app_context():
    db.create_all()

UPLOAD = app.config["UPLOAD_FOLDER"]
STATIC = app.config["STATIC_CLOTHING"]

os.makedirs(UPLOAD, exist_ok=True)
os.makedirs(STATIC, exist_ok=True)


@app.route("/")
def index():
    return {"status": "AI Try-On Backend Running 🚀"}


@app.route("/health")
def health():
    return {"status": "ok"}


# ==============================
# STATIC FILE
# ==============================
@app.route("/static/clothing/<path:filename>")
def static_clothing(filename):
    try:
        return send_from_directory(
            app.config["STATIC_CLOTHING"],
            filename
        )
    except Exception as e:
        print("STATIC ERROR:", e)
        return {"msg": "File not found"}, 404


# ==============================
# SIZE ESTIMATION (MANUAL FALLBACK)
# ==============================
def estimate_size_from_manual(m):
    try:
        ld = float(m.get("ld") or 0)
        tinggi = float(m.get("tinggi") or 165)
        pinggang = float(m.get("pinggang") or 0)
        pinggul = float(m.get("pinggul") or 0)
        arm = float(m.get("arm") or 0)
        front = float(m.get("front_width") or 0)
        back = float(m.get("back_width") or 0)

        sizes = []

        def classify(v, ranges):
            for size, (low, high) in ranges.items():
                if low <= v <= high:
                    return size
            return "XXXL"

        size_ranges = {
            "chest": {
                "S": (75, 85),
                "M": (80, 88),
                "L": (87, 102),
                "XL": (102, 110),
                "XXL": (110, 124),
            },
            "waist": {
                "S": (65, 72),
                "M": (73, 79),
                "L": (77, 100),
                "XL": (95, 102),
                "XXL": (102, 115),
            },
            "hip": {
                "S": (87, 92),
                "M": (91, 97),
                "L": (96, 106),
                "XL": (106, 115),
                "XXL": (115, 134),
            },
            "arm": {
                "S": (27, 30),
                "M": (30, 32),
                "L": (31, 38),
                "XL": (38, 41),
                "XXL": (41, 47),
            },
            "front": {
                "S": (32, 41),
                "M": (39, 41),
                "L": (34, 46),
                "XL": (37, 40),
                "XXL": (40, 50),
            },
            "back": {
                "S": (33, 48),
                "M": (40, 48),
                "L": (37, 49),
                "XL": (39, 41),
                "XXL": (40, 54),
            }
        }

        if ld > 0:
            sizes.append(classify(ld, size_ranges["chest"]))

        if pinggang > 0:
            sizes.append(classify(pinggang, size_ranges["waist"]))

        if pinggul > 0:
            sizes.append(classify(pinggul, size_ranges["hip"]))

        if arm > 0:
            sizes.append(classify(arm, size_ranges["arm"]))

        if front > 0:
            sizes.append(classify(front, size_ranges["front"]))

        if back > 0:
            sizes.append(classify(back, size_ranges["back"]))

        if not sizes:
            return "M"

        order = {
            "S": 1,
            "M": 2,
            "L": 3,
            "XL": 4,
            "XXL": 5,
            "XXXL": 6
        }

        size = max(sizes, key=lambda x: order[x])

        if tinggi > 175 and size in ["S", "M", "L"]:
            size = next_size(size)

        print("MANUAL SIZE LIST:", sizes)
        print("FINAL MANUAL SIZE:", size)

        return size

    except Exception as e:
        print("MANUAL SIZE ERROR:", e)
        return "M"


def next_size(size):
    order = ["S", "M", "L", "XL", "XXL", "XXXL"]

    if size in order and size != "XXXL":
        return order[order.index(size) + 1]

    return size


# ==============================
# BODY FILTER
# ==============================
def adjust_recommendation_by_body(shape, items):
    if not isinstance(items, list):
        return []

    if shape == "inverted_triangle":
        return [
            i for i in items
            if i.get("type") != "shoulder_focus"
        ]

    if shape == "pear":
        return [
            i for i in items
            if i.get("type") != "hip_focus"
        ]

    return items


# ==============================
# ANALYZE
# ==============================
@app.route("/api/analyze", methods=["POST"])
def analyze():
    try:
        from detectors.skin_detector import detect_skin_tone

        if "body_image" not in request.files:
            return {"msg": "body_image required"}, 400

        body_img = request.files["body_image"]
        face_img = request.files.get("face_image")
        gender = request.form.get("gender", "female")

        manual = {
            "tinggi": request.form.get("tinggi"),
            "ld": request.form.get("ld"),
            "pinggang": request.form.get("pinggang"),
            "pinggul": request.form.get("pinggul"),
            "arm": request.form.get("arm"),
            "front_width": request.form.get("front_width"),
            "back_width": request.form.get("back_width"),
        }

        def to_float(v):
            try:
                return float(v)
            except:
                return None

        measurements = {
            "chest_cm": to_float(manual.get("ld")),
            "waist_cm": to_float(manual.get("pinggang")),
            "hip_cm": to_float(manual.get("pinggul")),
            "arm_cm": to_float(manual.get("arm")),
            "front_width_cm": to_float(manual.get("front_width")),
            "back_width_cm": to_float(manual.get("back_width")),
        }

        print("RAW FORM:", request.form)
        print("MEASUREMENTS:", measurements)

        body_path = os.path.join(
            UPLOAD,
            f"{uuid4().hex}.jpg"
        )
        body_img.save(body_path)

        face_path = None

        if face_img:
            face_path = os.path.join(
                UPLOAD,
                f"{uuid4().hex}.jpg"
            )
            face_img.save(face_path)

        # ==============================
        # SKIN
        # ==============================
        skin_tone = "unknown"
        undertone = "neutral"

        if face_path:
            try:
                skin_data = detect_skin_tone(face_path)

                if isinstance(skin_data, dict):
                    skin_tone = skin_data.get("tone", "unknown")
                    undertone = skin_data.get("undertone", "neutral")

            except Exception as e:
                print("SKIN ERROR:", e)

        # ==============================
        # BODY SHAPE
        # ==============================
        try:
            shape, source, probs = detect_body_shape(
                body_path,
                measurements["chest_cm"],
                measurements["waist_cm"],
                measurements["hip_cm"]
            )

        except Exception as e:
            print("BODY SHAPE ERROR:", e)
            shape, source, probs = (
                "unknown",
                "fallback",
                {}
            )

        # ==============================
        # SIZE
        # ==============================
        size_estimate = predict_size(measurements)

        if not size_estimate:
            size_estimate = estimate_size_from_manual(manual)

        print("FINAL SIZE ESTIMATE:", size_estimate)

        # ==============================
        # RECOMMEND
        # ==============================
        recommendations = recommend(
            skin_tone,
            shape,
            size_estimate,
            gender
        ) or []

        recommendations = adjust_recommendation_by_body(
            shape,
            recommendations
        )

        # ==============================
        # CLEANUP
        # ==============================
        if os.path.exists(body_path):
            os.remove(body_path)

        if face_path and os.path.exists(face_path):
            os.remove(face_path)

        return jsonify({
            "skin_tone": skin_tone,
            "undertone": undertone,
            "body_shape": shape,
            "size_estimate": size_estimate,
            "recommendations": recommendations
        })

    except Exception as e:
        print("ANALYZE ERROR:", e)
        return {"error": str(e)}, 500


# ==============================
# FINAL RESULT
# ==============================
@app.route("/api/final_result", methods=["POST"])
def final_result():
    data = request.json or {}

    return jsonify({
        "skin_tone": data.get("skin_tone"),
        "undertone": data.get("undertone"),
        "body_shape": data.get("body_shape"),
        "size": data.get("size"),
        "selected_outfit": data.get("selected_outfit"),
        "tryon_image": data.get("tryon_image")
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )