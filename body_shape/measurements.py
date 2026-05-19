def body_shape_from_measurements(chest, waist, hip):
    try:
        chest = float(chest) if chest else None
        waist = float(waist) if waist else None
        hip = float(hip) if hip else None

        if not chest or not waist or not hip:
            return None

        if waist >= chest and waist >= hip:
            return "apple"

        if abs(chest - hip) <= 5 and waist <= min(chest, hip) * 0.75:
            return "hourglass"

        if hip - chest >= 7:
            return "pear"

        if chest - hip >= 7:
            return "inverted_triangle"

        if abs(chest - waist) < 8 and abs(waist - hip) < 8:
            return "rectangle"

        return "rectangle"

    except Exception as e:
        print("ERROR:", e)
        return None