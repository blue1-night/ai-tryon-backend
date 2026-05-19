from app import app, db
# import aplikasi Flask dan database

from models import Clothing
# import model Clothing


with app.app_context():
    # memastikan context Flask aktif (wajib untuk DB)

    db.create_all()
    # membuat tabel jika belum ada

    clothes = [
        Clothing(
            name="kebaya_rose_gold",
            gender="female",
            size="S,M,L",
            skin_tone="all",
            body_shape="pear,hourglass,rectangle",
            image_filename="kebaya_rose_gold.png"
        ),
        # data pakaian 1

        Clothing(
            name="kebaya_moka",
            gender="female",
            size="S,M,L,XL",
            skin_tone="all",
            body_shape="hourglass,rectangle,pear",
            image_filename="kebaya_moka.png"
        ),

        Clothing(
            name="kebaya_merah_marun_payet",
            gender="female",
            size="M,L,XL",
            skin_tone="all",
            body_shape="apple,rectangle,pear",
            image_filename="kebaya_merah_marun_payet.png"
        ),

        Clothing(
            name="kebaya_hijau_zaitun_berpayet",
            gender="female",
            size="M,L,XL",
            skin_tone="all",
            body_shape="apple,rectangle,pear",
            image_filename="kebaya_hijau_zaitun_berpayet.png"
        )
    ]

    db.session.add_all(clothes)
    # memasukkan semua data ke database

    db.session.commit()
    # simpan perubahan

    print("✅ Clothing data inserted successfully")