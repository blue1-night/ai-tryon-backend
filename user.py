from models import db
import re


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100), unique=True, nullable=False)

    password_hash = db.Column(db.String(255), nullable=False)

    role = db.Column(db.String(20), default="user")


    def set_password(self, password):
        if not password:
            raise ValueError("Password wajib diisi")

        if len(password) < 6:
            raise ValueError("Password minimal 6 karakter")

        if not re.search(r"[A-Z]", password):
            raise ValueError("Password harus mengandung huruf besar")

        if not re.search(r"[a-z]", password):
            raise ValueError("Password harus mengandung huruf kecil")

        if not re.search(r"[0-9]", password):
            raise ValueError("Password harus mengandung angka")

        # sesuai permintaan: plaintext
        self.password_hash = password


    def check_password(self, password):
        if not password:
            return False

        return self.password_hash == password