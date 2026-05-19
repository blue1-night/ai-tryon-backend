from models import Clothing
from flask import current_app


def match_field(field_value, user_value):

    if not field_value:
        return False

    values = [
        v.strip().lower()
        for v in str(field_value).split(",")
    ]

    if "all" in values:
        return True

    return (
        user_value and
        user_value.lower() in values
    )


def match_size(field_value, user_value):

    if not field_value:
        return False

    values = [
        v.strip().upper()
        for v in str(field_value).split(",")
    ]

    if "ALL" in values:
        return True

    return (
        user_value and
        user_value.upper() in values
    )


def recommend(
    skin_tone,
    body_shape,
    size_estimate,
    gender,
):

    items = Clothing.query.filter_by(
        gender=gender
    ).all()

    results = []

    base_url = current_app.config["BASE_URL"]

    for c in items:

        # ================= SKIN =================
        if skin_tone and not match_field(
            c.skin_tone,
            skin_tone,
        ):
            continue

        # ================= BODY =================
        if body_shape and not match_field(
            c.body_shape,
            body_shape,
        ):
            continue

        # ================= SIZE =================
        if size_estimate and not match_size(
            c.size,
            size_estimate,
        ):
            continue

        # ================= IMAGE URL =================
        image_url = ""

        if c.image_filename:
            image_url = (
                f"{base_url}/static/clothing/"
                f"{c.image_filename}"
            )

        # ================= FULL DATA =================
        results.append({

            "id": c.id,

            "name": c.name,

            "category": c.category,

            "gender": c.gender,

            "size": c.size,

            "skin_tone": c.skin_tone,

            "body_shape": c.body_shape,

            "image_filename": c.image_filename,

            "image_url": image_url,
        })

    return results