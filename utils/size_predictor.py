from utils.size_chart import get_size_chart


def in_range(val, r):
    if val is None:
        return False
    return r[0] <= val <= r[1]


def size_rank(size):
    order = {
        "XS": 1,
        "S": 2,
        "M": 3,
        "L": 4,
        "XL": 5,
        "XXL": 6,
        "XXXL": 7
    }
    return order.get(size, 0)


def find_size_for_value(value, field, chart):
    if value is None:
        return None

    for size, r in chart.items():
        if field in r and in_range(value, r[field]):
            return size

    return "XXXL"


def predict_size(measurements):
    chart = get_size_chart()

    chest = measurements.get("chest_cm")
    waist = measurements.get("waist_cm")
    hip = measurements.get("hip_cm")
    arm = measurements.get("arm_cm")
    # armpit = measurements.get("armpit_cm")
    front = measurements.get("front_width_cm")
    back = measurements.get("back_width_cm")

    sizes = []

    fields = {
        "chest": chest,
        "waist": waist,
        "hip": hip,
        "arm": arm,
        # "armpit": armpit,
        "front_width": front,
        "back_width": back,
    }

    for field, value in fields.items():
        size = find_size_for_value(value, field, chart)
        if size:
            sizes.append(size)

    if not sizes:
        return None

    largest = max(sizes, key=size_rank)

    print("SIZE PER PARAMETER:", sizes)
    print("FINAL SIZE:", largest)

    return largest