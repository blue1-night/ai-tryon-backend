import os
import time
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

from models import db, Clothing

# ==============================
# INIT BLUEPRINT
# ==============================
admin_clothing_bp = Blueprint(
    "admin_clothing",
    __name__,
    url_prefix="/auth/admin/clothing"
)

# ==============================
# PREFLIGHT
# ==============================
@admin_clothing_bp.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        return "", 200


# ==============================
# ADMIN GUARD
# ==============================
def admin_only():
    claims = get_jwt()
    if not claims or claims.get("role") != "admin":
        return jsonify({"msg": "Admin access required"}), 403
    return None


ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}


# ==============================
# ERROR HANDLER
# ==============================
@admin_clothing_bp.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    return jsonify({"msg": "File terlalu besar"}), 413


# ==============================
# GET ALL
# ==============================
@admin_clothing_bp.route("/", methods=["GET"])
@jwt_required()
def get_clothing():
    if (resp := admin_only()):
        return resp

    try:
        clothes = Clothing.query.filter(
            (Clothing.is_deleted == False) | (Clothing.is_deleted.is_(None))
        ).all()
    except Exception as e:
        print("GET FILTER ERROR:", e)
        clothes = Clothing.query.all()

    return jsonify([
        {
            "id": c.id,
            "name": c.name,
            "gender": c.gender,
            "category": c.category,
            "skin_tone": c.skin_tone,
            "body_shape": c.body_shape,
            "size": c.size,
            "image_filename": c.image_filename,
            "image_url": f"http://localhost:5000/static/clothing/{c.image_filename}"
        }
        for c in clothes
    ]), 200


# ==============================
# ADD
# ==============================
@admin_clothing_bp.route("/", methods=["POST"])
@jwt_required()
def add_clothing():
    if (resp := admin_only()):
        return resp

    name = request.form.get("name")
    gender = request.form.get("gender")
    category = request.form.get("category")
    skin_tone = request.form.get("skin_tone")
    body_shape = request.form.get("body_shape")
    size = request.form.get("size")
    image = request.files.get("image")

    if not name or not gender or not category or not image:
        return jsonify({"msg": "Field wajib belum lengkap"}), 400

    filename = secure_filename(image.filename)

    if "." not in filename:
        return jsonify({"msg": "File tidak valid"}), 400

    # 🔥 FIX UTAMA (AMAN & BERSIH)
    name_only, ext = os.path.splitext(filename)
    ext = ext.replace(".", "").lower()

    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({"msg": "Format harus PNG/JPG/JPEG"}), 400

    timestamp = int(time.time())
    new_filename = f"{name_only}_{timestamp}.{ext}"

    save_dir = current_app.config.get("STATIC_CLOTHING")
    os.makedirs(save_dir, exist_ok=True)

    save_path = os.path.join(save_dir, new_filename)
    image.save(save_path)

    print("SAVED:", save_path)

    clothing = Clothing(
        name=name.strip(),
        gender=gender.strip(),
        category=category.strip(),
        skin_tone=skin_tone.strip() if skin_tone else None,
        body_shape=body_shape.strip() if body_shape else None,
        size=size.strip() if size else None,
        image_filename=new_filename
    )

    db.session.add(clothing)
    db.session.commit()

    return jsonify({"msg": "Clothing added"}), 201


# ==============================
# DELETE
# ==============================
@admin_clothing_bp.route("/<int:clothing_id>", methods=["DELETE"])
@jwt_required()
def delete_clothing(clothing_id):
    if (resp := admin_only()):
        return resp

    clothing = Clothing.query.get_or_404(clothing_id)

    db.session.delete(clothing)
    db.session.commit()

    return jsonify({"msg": "Clothing deleted (file preserved)"}), 200


# ==============================
# UPDATE
# ==============================
@admin_clothing_bp.route("/<int:clothing_id>", methods=["PUT"])
@jwt_required()
def update_clothing(clothing_id):
    if (resp := admin_only()):
        return resp

    clothing = Clothing.query.get_or_404(clothing_id)

    name = request.form.get("name")
    gender = request.form.get("gender")
    category = request.form.get("category")
    skin_tone = request.form.get("skin_tone")
    body_shape = request.form.get("body_shape")
    size = request.form.get("size")
    image = request.files.get("image")

    if name is not None:
        clothing.name = name.strip()
    if gender is not None:
        clothing.gender = gender.strip()
    if category is not None:
        clothing.category = category.strip()
    if skin_tone is not None:
        clothing.skin_tone = skin_tone.strip() if skin_tone else None
    if body_shape is not None:
        clothing.body_shape = body_shape.strip() if body_shape else None
    if size is not None:
        clothing.size = size.strip()

    if image:
        filename = secure_filename(image.filename)

        if "." not in filename:
            return jsonify({"msg": "File tidak valid"}), 400

        # 🔥 FIX UTAMA (SAMA SEPERTI ADD)
        name_only, ext = os.path.splitext(filename)
        ext = ext.replace(".", "").lower()

        if ext not in ALLOWED_EXTENSIONS:
            return jsonify({"msg": "Format harus PNG/JPG/JPEG"}), 400

        timestamp = int(time.time())
        new_filename = f"{name_only}_{timestamp}.{ext}"

        save_path = os.path.join(
            current_app.config.get("STATIC_CLOTHING", ""),
            new_filename
        )

        image.save(save_path)

        print("UPDATED IMAGE:", save_path)

        clothing.image_filename = new_filename

    db.session.commit()
    return jsonify({"msg": "Clothing updated"}), 200