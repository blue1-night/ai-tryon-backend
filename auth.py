from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from models import db
from user import User
import traceback

auth_bp = Blueprint("auth", __name__)


# =========================
# HELPER: SANITIZE DATA
# =========================
def safe_log(data):
    if not data:
        return {}

    safe = dict(data)

    if "password" in safe:
        safe["password"] = "*****"

    return safe


# =========================
# REGISTER
# =========================
@auth_bp.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json(silent=True)

        print("REGISTER DATA:", safe_log(data))

        if not data:
            return jsonify({
                "msg": "Request body harus JSON"
            }), 400

        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify({
                "msg": "Username dan password wajib diisi"
            }), 400

        username = username.strip()

        if username == "":
            return jsonify({
                "msg": "Username tidak boleh kosong"
            }), 400

        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            return jsonify({
                "msg": "Username sudah terdaftar"
            }), 409

        user = User(
            username=username,
            role="user"
        )

        try:
            user.set_password(password)
        except ValueError as e:
            return jsonify({
                "msg": str(e)
            }), 400

        db.session.add(user)
        db.session.commit()

        print("REGISTER SUCCESS:", username)

        return jsonify({
            "msg": "Registrasi berhasil"
        }), 201

    except Exception as e:
        db.session.rollback()
        traceback.print_exc()

        return jsonify({
            "msg": "Register gagal",
            "error": str(e)
        }), 500


# =========================
# LOGIN
# =========================
@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json(silent=True)

        print("LOGIN DATA:", safe_log(data))

        if not data:
            return jsonify({
                "msg": "Request body harus JSON"
            }), 400

        username = data.get("username")
        password = data.get("password")
        login_type = data.get("type")

        if not username or not password:
            return jsonify({
                "msg": "Username dan password wajib diisi"
            }), 400

        username = username.strip()

        user = User.query.filter_by(username=username).first()

        if not user:
            return jsonify({
                "msg": "Username atau password salah"
            }), 401

        if not user.check_password(password):
            return jsonify({
                "msg": "Username atau password salah"
            }), 401

        if login_type == "admin" and user.role != "admin":
            return jsonify({
                "msg": "Akses admin ditolak"
            }), 403

        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={
                "username": user.username,
                "role": user.role
            }
        )

        print("LOGIN SUCCESS:", user.username, user.role)

        return jsonify({
            "access_token": access_token,
            "username": user.username,
            "role": user.role
        }), 200

    except Exception as e:
        traceback.print_exc()

        return jsonify({
            "msg": "Login gagal",
            "error": str(e)
        }), 500


# =========================
# FORGOT PASSWORD
# =========================
@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    try:
        data = request.get_json(silent=True)

        print("RESET DATA:", safe_log(data))

        if not data:
            return jsonify({
                "msg": "Request body harus JSON"
            }), 400

        username = data.get("username")
        new_password = data.get("password")

        if not username or not new_password:
            return jsonify({
                "msg": "Username dan password baru wajib diisi"
            }), 400

        username = username.strip()

        if username == "":
            return jsonify({
                "msg": "Username tidak boleh kosong"
            }), 400

        user = User.query.filter_by(username=username).first()

        if not user:
            return jsonify({
                "msg": "User tidak ditemukan"
            }), 404

        try:
            user.set_password(new_password)
        except ValueError as e:
            return jsonify({
                "msg": str(e)
            }), 400

        db.session.commit()

        print("RESET SUCCESS:", username)

        return jsonify({
            "msg": "Password berhasil direset"
        }), 200

    except Exception as e:
        db.session.rollback()
        traceback.print_exc()

        return jsonify({
            "msg": "Reset password gagal",
            "error": str(e)
        }), 500