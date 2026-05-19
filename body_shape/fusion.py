from body_shape.visual import body_shape_from_image
from body_shape.measurements import body_shape_from_measurements

def detect_body_shape(image=None, chest=None, waist=None, hip=None):
    has_image = image is not None

    has_measurements = (
        chest not in [None, "", 0] and
        waist not in [None, "", 0] and
        hip not in [None, "", 0]
    )

    shapes = [
        "apple",
        "hourglass",
        "pear",
        "inverted_triangle",
        "rectangle"
    ]

    # ==============================
    # CASE 1: FOTO + UKURAN
    # ==============================
    if has_image and has_measurements:

        try:
            visual_shape, visual_conf = body_shape_from_image(image)

            if visual_conf is None:
                visual_conf = 0.5

        except:
            visual_shape, visual_conf = None, 0.0

        try:
            measure_shape = body_shape_from_measurements(
                chest,
                waist,
                hip
            )
        except:
            measure_shape = "rectangle"

        # ==============================
        # WEIGHT LEBIH STABIL
        # ==============================
        weight_measure = 0.75
        weight_visual = 0.25

        scores = {s: 0.0 for s in shapes}

        # ==============================
        # VISUAL SCORE
        # ==============================
        if visual_shape in shapes:
            scores[visual_shape] += (
                visual_conf * weight_visual
            )

        # ==============================
        # MEASUREMENT SCORE
        # ==============================
        if measure_shape in shapes:
            scores[measure_shape] += weight_measure

        # ==============================
        # NORMALISASI
        # ==============================
        total = sum(scores.values())

        if total <= 0:
            total = 1.0

        probs = {
            k: round(v / total, 3)
            for k, v in scores.items()
        }

        # ==============================
        # FINAL SHAPE
        # ==============================
        final_shape = max(probs, key=probs.get)

        return final_shape, "probabilistic_fusion", probs

    # ==============================
    # CASE 2: FOTO SAJA
    # ==============================
    if has_image:

        try:
            shape, conf = body_shape_from_image(image)

            if conf is None:
                conf = 0.6

            scores = {s: 0.0 for s in shapes}

            if shape in shapes:
                scores[shape] = conf

            total = sum(scores.values())

            if total <= 0:
                total = 1.0

            probs = {
                k: round(v / total, 3)
                for k, v in scores.items()
            }

            final_shape = max(probs, key=probs.get)

            return final_shape, "image_only", probs

        except:
            pass

        return "rectangle", "fallback", {
            s: 0.0 for s in shapes
        }

    # ==============================
    # CASE 3: UKURAN SAJA
    # ==============================
    if has_measurements:

        shape = body_shape_from_measurements(
            chest,
            waist,
            hip
        )

        scores = {s: 0.0 for s in shapes}

        if shape in shapes:
            scores[shape] = 1.0

        return shape, "measurement_only", scores

    raise ValueError("Image or measurements required")