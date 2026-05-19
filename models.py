from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Clothing(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100))
    gender = db.Column(db.String(10))
    size = db.Column(db.String(50))
    skin_tone = db.Column(db.String(100))
    body_shape = db.Column(db.String(50))
    image_filename = db.Column(db.String(200))
    category = db.Column(db.String(50), default="pesta")

    # 🔥 SOFT DELETE
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)