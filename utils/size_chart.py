def get_size_chart():
    # fungsi untuk mengambil data standar ukuran pakaian
    return {
        "S": {  # ukuran Small
            "chest": (75, 85),       # lingkar dada dalam cm
            "waist": (65, 72),       # lingkar pinggang
            "hip": (87, 92),         # lingkar pinggul
            "arm": (27, 30),         # panjang lengan
            "armpit": (36, 41),      # lingkar ketiak
            "front_width": (32, 41), # lebar depan
            "back_width": (33, 48),  # lebar belakang
        },
        "M": {  # Medium
            "chest": (80, 88),
            "waist": (73, 79),
            "hip": (91, 97),
            "arm": (30, 32),
            "armpit": (36, 46),
            "front_width": (39, 41),
            "back_width": (40, 48),
        },
        "L": {
            "chest": (87, 102),
            "waist": (77, 100),
            "hip": (96, 106),
            "arm": (31, 38),
            "armpit": (39, 47),
            "front_width": (34, 46),
            "back_width": (37, 49),
        },
        "XL": {
            "chest": (102, 110),
            "waist": (95, 102),
            "hip": (106, 115),
            "arm": (38, 41),
            "armpit": (45, 50),
            "front_width": (37, 40),
            "back_width": (39, 41),
        },
        "XXL": {
            "chest": (110, 124),
            "waist": (102, 115),
            "hip": (115, 134),
            "arm": (41, 47),
            "armpit": (50, 60),
            "front_width": (40, 50),
            "back_width": (40, 54),
        },
        "XXXL": {
            "chest": (124, 999),   # 999 = tanpa batas atas
            "waist": (115, 999),
            "hip": (134, 999),
            "arm": (47, 999),
            "armpit": (60, 999),
            "front_width": (50, 999),
            "back_width": (54, 999),
        }
    }