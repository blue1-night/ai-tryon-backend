from datetime import timedelta
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "jwt-secret-key")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)

    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR,'data.sqlite')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    OUTPUT_FOLDER = os.path.join(BASE_DIR, "outputs")

    STATIC_CLOTHING = os.path.join(BASE_DIR, "static", "clothing")

    BASE_URL = os.environ.get(
        "BASE_URL",
        "http://103.55.38.102"
    )

    MAX_CONTENT_LENGTH = 20 * 1024 * 1024