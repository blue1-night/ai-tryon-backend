from models import db
# import database

import re
# regex (validasi password)


class User(db.Model):
    # tabel user

    id = db.Column(db.Integer, primary_key=True)
    # ID user

    username = db.Column(db.String(100), unique=True, nullable=False)
    # username unik

    password_hash = db.Column(db.String(255), nullable=False)
    # password disimpan plain text (nama kolom tetap)

    role = db.Column(db.String(20), default="user")
    # role user (admin / user)


    def set_password(self, password):
        # VALIDASI PASSWORD

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

        # SIMPAN TANPA HASH
        self.password_hash = password


    def check_password(self, password):
        # cek password plain text

        if not password:
            return False

        return self.password_hash == password