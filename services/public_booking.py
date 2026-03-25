from urllib.parse import quote


RESTAURANT_PROFILE = {
    "name": "Manna Bakery and Cafe",
    "tagline": "Tempat nyaman untuk ngopi, makan santai, acara keluarga, dan reservasi rombongan.",
    "description": "Laman ini dibuat sebagai tampilan publik agar tamu bisa booking meja, melihat alamat, dan langsung chat WhatsApp Manna Bakery and Cafe.",
    "address": "Jl. Taman Bunga, Moodu, Kec. Kota Tim., Kota Gorontalo, Gorontalo, Indonesia",
    "maps_url": "https://www.google.com/maps/place/Manna+Bakery+%26+Cafe/@0.5422788,123.0706622,18z/data=!4m15!1m8!3m7!1s0x32792b2581d491e9:0xe903578a06130f2f!2sJl.+Taman+Bunga,+Kec.+Kota+Tim.,+Kota+Gorontalo,+Gorontalo+96135!3b1!8m2!3d0.5433483!4d123.07236!16s%2Fg%2F11cn8tf56c!3m5!1s0x32792ba4ec34408f:0x5e8e69efd821cdbf!8m2!3d0.5415071!4d123.0705396!16s%2Fg%2F11j3q8ccyk?entry=ttu&g_ep=EgoyMDI2MDMyMi4wIKXMDSoASAFQAw%3D%3D",
    "whatsapp_number": "628113112919",
    "whatsapp_display": "08113112919",
    "hours": [
        {"label": "Senin - Jumat", "value": "10.00 - 22.00"},
        {"label": "Sabtu - Minggu", "value": "09.00 - 23.00"},
        {"label": "Reservasi Grup", "value": "Sebaiknya booking lebih awal"},
    ],
    "features": [
        {
            "title": "Booking Mudah",
            "description": "Isi form singkat untuk kirim permintaan reservasi langsung ke sistem restoran.",
        },
        {
            "title": "Chat WhatsApp",
            "description": "Tamu bisa langsung menghubungi restoran untuk konfirmasi cepat atau tanya ketersediaan.",
        },
        {
            "title": "Info Lokasi",
            "description": "Alamat, jam operasional, dan akses ke Google Maps tersedia dalam satu halaman.",
        },
    ],
    "highlights": [
        "Area makan nyaman untuk keluarga dan rombongan.",
        "Bisa dipakai untuk acara kecil, meeting, dan dinner santai.",
        "Admin tetap dapat masuk ke panel operasional restoran dari laman ini.",
    ],
}


def get_restaurant_whatsapp_link(message="Halo Manna Bakery and Cafe, saya ingin tanya reservasi meja."):
    return f"https://wa.me/{RESTAURANT_PROFILE['whatsapp_number']}?text={quote(message)}"


def build_public_booking_description(whatsapp_number, seating_preference, notes):
    parts = ["Sumber: Website Booking"]

    if whatsapp_number:
        parts.append(f"WhatsApp: {whatsapp_number}")

    if seating_preference:
        parts.append(f"Preferensi meja: {seating_preference}")

    if notes:
        parts.append(f"Catatan: {notes}")

    return " | ".join(parts)
