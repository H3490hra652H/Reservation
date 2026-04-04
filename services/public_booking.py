import json
import re
from collections import OrderedDict
from datetime import datetime, timedelta
from urllib.parse import quote

from services.common import format_currency, format_menu_label, format_weight_display, normalize_text
from services.menu_options import resolve_menu_submission
from services.stock import (
    ensure_additional_stock_tables,
    format_size_category_label,
    get_special_tuna_stock_context,
    get_stock_context,
    reduce_stock_after_order,
    resolve_selected_stock_refs,
    validate_stock_request,
)


DEFAULT_BOOKING_DURATION_HOURS = 2
BOOKING_TABLE_AREA = "Ruang Utama"
BOOKING_VIP_AREA = "VIP 1"
BOOKING_VIP_SECOND_AREA = "VIP 2"
BOOKING_HALL_AREA = "Hall"
BOOKING_OUTDOOR_AREA = "Outdoor"
BOOKING_CANOPY_AREA = "Kanopi"
VIP_MAX_GUESTS = 50
LARGE_PARTY_ALLOWED_AREAS = [BOOKING_HALL_AREA, BOOKING_OUTDOOR_AREA, BOOKING_TABLE_AREA]
LARGE_PARTY_BLOCKED_AREAS = [BOOKING_VIP_AREA, BOOKING_VIP_SECOND_AREA, BOOKING_CANOPY_AREA]

PUBLIC_MENU_GROUPS = [
    {"key": "ayam", "label": "Menu Ayam", "order": 10},
    {"key": "ikan_nila", "label": "Menu Ikan Nila", "order": 20},
    {"key": "seafood", "label": "Menu Seafood", "order": 30},
    {"key": "daging", "label": "Menu Daging", "order": 40},
    {"key": "taiwan_dish", "label": "Taiwan Dish", "order": 50},
    {"key": "menu_sampingan", "label": "Menu Sampingan", "order": 60},
    {"key": "soup_sayur", "label": "Soup dan Sayur", "order": 70},
    {"key": "nasi_mie_bubur", "label": "Nasi, Mie, dan Bubur", "order": 80},
    {"key": "snack", "label": "Snack", "order": 90},
    {"key": "dessert", "label": "Dessert", "order": 100},
    {"key": "minuman_koffie", "label": "Minuman dan Koffie", "order": 110},
    {"key": "non_koffie", "label": "Non Koffie", "order": 120},
]
PUBLIC_MENU_GROUP_LOOKUP = {item["key"]: item for item in PUBLIC_MENU_GROUPS}

DEFAULT_BOOKING_RESOURCES = [
    {"resource_code": "main-01", "area_name": BOOKING_TABLE_AREA, "resource_type": "table", "display_name": "Meja 1", "table_label": "1", "seat_capacity": 4, "setup_key": None, "image_url": None, "description": "4 kursi. Dekat AC dan panggung live music.", "sort_order": 10},
    {"resource_code": "main-02", "area_name": BOOKING_TABLE_AREA, "resource_type": "table", "display_name": "Meja 2", "table_label": "2", "seat_capacity": 4, "setup_key": None, "image_url": None, "description": "4 kursi. Dekat AC dan panggung live music.", "sort_order": 20},
    {"resource_code": "main-03", "area_name": BOOKING_TABLE_AREA, "resource_type": "table", "display_name": "Meja 3", "table_label": "3", "seat_capacity": 4, "setup_key": None, "image_url": None, "description": "4 kursi. Dekat AC dan panggung live music.", "sort_order": 30},
    {"resource_code": "main-04", "area_name": BOOKING_TABLE_AREA, "resource_type": "table", "display_name": "Meja 4", "table_label": "4", "seat_capacity": 4, "setup_key": None, "image_url": None, "description": "4 kursi. Dekat AC dan panggung live music.", "sort_order": 40},
    {"resource_code": "main-05", "area_name": BOOKING_TABLE_AREA, "resource_type": "table", "display_name": "Meja 5", "table_label": "5", "seat_capacity": 4, "setup_key": None, "image_url": None, "description": "4 kursi. Dekat AC dan panggung live music.", "sort_order": 50},
    {"resource_code": "main-06", "area_name": BOOKING_TABLE_AREA, "resource_type": "table", "display_name": "Meja 6", "table_label": "6", "seat_capacity": 4, "setup_key": None, "image_url": None, "description": "4 kursi. Dekat AC dan panggung live music.", "sort_order": 60},
    {"resource_code": "main-07", "area_name": BOOKING_TABLE_AREA, "resource_type": "table", "display_name": "Meja 7", "table_label": "7", "seat_capacity": 4, "setup_key": None, "image_url": None, "description": "4 kursi. Dekat kasir, bar, dan pajangan roti.", "sort_order": 70},
    {"resource_code": "main-08", "area_name": BOOKING_TABLE_AREA, "resource_type": "table", "display_name": "Meja 8", "table_label": "8", "seat_capacity": 4, "setup_key": None, "image_url": None, "description": "4 kursi. Dekat kasir, bar, dan pajangan roti.", "sort_order": 80},
    {"resource_code": "main-09", "area_name": BOOKING_TABLE_AREA, "resource_type": "table", "display_name": "Meja 9", "table_label": "9", "seat_capacity": 4, "setup_key": None, "image_url": None, "description": "4 kursi. Dekat kasir, bar, dan pajangan roti.", "sort_order": 90},
    {"resource_code": "main-10", "area_name": BOOKING_TABLE_AREA, "resource_type": "table", "display_name": "Meja 10", "table_label": "10", "seat_capacity": 4, "setup_key": None, "image_url": None, "description": "4 kursi. Dekat kasir, bar, dan pajangan roti.", "sort_order": 100},
    {"resource_code": "main-11", "area_name": BOOKING_TABLE_AREA, "resource_type": "table", "display_name": "Meja 11", "table_label": "11", "seat_capacity": 4, "setup_key": None, "image_url": None, "description": "4 kursi. Dekat pintu masuk, jendela, dan panggung live music.", "sort_order": 110},
    {"resource_code": "main-12", "area_name": BOOKING_TABLE_AREA, "resource_type": "table", "display_name": "Meja 12", "table_label": "12", "seat_capacity": 4, "setup_key": None, "image_url": None, "description": "4 kursi. Dekat pintu masuk, jendela, dan panggung live music.", "sort_order": 120},
    {"resource_code": "vip-classroom", "area_name": BOOKING_VIP_AREA, "resource_type": "vip_setup", "display_name": "VIP 1 Ala Carte - Classroom", "table_label": None, "seat_capacity": 50, "setup_key": "classroom", "image_url": "https://images.unsplash.com/photo-1511578314322-379afb476865?auto=format&fit=crop&w=1200&q=80", "description": "Layanan ala carte dengan setup classroom. Maksimal 50 tamu.", "sort_order": 200},
    {"resource_code": "vip-letter-u", "area_name": BOOKING_VIP_AREA, "resource_type": "vip_setup", "display_name": "VIP 1 Ala Carte - Letter U", "table_label": None, "seat_capacity": 50, "setup_key": "letter_u", "image_url": "https://images.unsplash.com/photo-1517457373958-b7bdd4587205?auto=format&fit=crop&w=1200&q=80", "description": "Layanan ala carte dengan setup Letter U. Maksimal 50 tamu.", "sort_order": 210},
    {"resource_code": "vip-dining-table", "area_name": BOOKING_VIP_AREA, "resource_type": "vip_setup", "display_name": "VIP 1 Ala Carte - Meja Makan", "table_label": None, "seat_capacity": 50, "setup_key": "dining_table", "image_url": "https://images.unsplash.com/photo-1552566626-52f8b828add9?auto=format&fit=crop&w=1200&q=80", "description": "Layanan ala carte dengan setup meja makan. Maksimal 50 tamu.", "sort_order": 220},
    {"resource_code": "vip-prasmanan", "area_name": BOOKING_VIP_AREA, "resource_type": "vip_setup", "display_name": "VIP 1 Prasmanan", "table_label": None, "seat_capacity": 50, "setup_key": "prasmanan", "image_url": "https://images.unsplash.com/photo-1555244162-803834f70033?auto=format&fit=crop&w=1200&q=80", "description": "Layanan VIP 1 prasmanan. Cocok untuk acara privat dengan maksimal 50 tamu.", "sort_order": 230},
    {"resource_code": "hall-a", "area_name": BOOKING_HALL_AREA, "resource_type": "table", "display_name": "Hall A", "table_label": "A", "seat_capacity": 40, "setup_key": None, "description": "Area lebih luas untuk acara komunitas atau grup besar.", "sort_order": 300},
    {"resource_code": "hall-b", "area_name": BOOKING_HALL_AREA, "resource_type": "table", "display_name": "Hall B", "table_label": "B", "seat_capacity": 60, "setup_key": None, "description": "Pilihan hall besar untuk reservasi rombongan.", "sort_order": 310},
    {"resource_code": "outdoor-01", "area_name": BOOKING_OUTDOOR_AREA, "resource_type": "table", "display_name": "Outdoor 1", "table_label": "O1", "seat_capacity": 6, "setup_key": None, "description": "Area semi terbuka untuk suasana santai.", "sort_order": 400},
    {"resource_code": "outdoor-02", "area_name": BOOKING_OUTDOOR_AREA, "resource_type": "table", "display_name": "Outdoor 2", "table_label": "O2", "seat_capacity": 8, "setup_key": None, "description": "Cocok untuk tamu yang ingin duduk di area luar.", "sort_order": 410},
    {"resource_code": "kanopi-01", "area_name": BOOKING_CANOPY_AREA, "resource_type": "table", "display_name": "Kanopi 1", "table_label": "K1", "seat_capacity": 8, "setup_key": None, "description": "Area teduh dengan sirkulasi udara lebih terbuka.", "sort_order": 500},
    {"resource_code": "kanopi-02", "area_name": BOOKING_CANOPY_AREA, "resource_type": "table", "display_name": "Kanopi 2", "table_label": "K2", "seat_capacity": 10, "setup_key": None, "description": "Pilihan area kanopi untuk grup kecil menengah.", "sort_order": 510},
]

RESTAURANT_PROFILE = {
    "name": "Manna Bakery and Cafe",
    "tagline": "Tempat nyaman untuk ngopi, makan santai, acara keluarga, dan reservasi rombongan.",
    "description": "Laman ini dibuat sebagai tampilan publik agar tamu bisa booking meja, memilih menu, melihat alamat, dan langsung chat WhatsApp Manna Bakery and Cafe.",
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
        {"title": "Booking Mudah", "description": "Isi data pemesan, pilih tempat, lalu kirim reservasi langsung ke sistem restoran."},
        {"title": "Digital Menu", "description": "Menu tampil seperti buku menu digital dan hanya menampilkan pilihan yang sesuai stok."},
        {"title": "Ketersediaan Tempat", "description": "Meja atau setup VIP yang sudah dipakai akan tampil not available sampai waktu booking selesai."},
    ],
    "highlights": [
        "Area makan nyaman untuk keluarga dan rombongan.",
        "Pilihan ruang utama, VIP 1, hall, outdoor, dan kanopi tersedia dalam satu form booking.",
        "Admin dapat melihat detail tamu, WhatsApp, slot booking, dan menu dari panel reservasi.",
    ],
}


def get_restaurant_whatsapp_link(message="Halo Manna Bakery and Cafe, saya ingin tanya reservasi meja."):
    return f"https://wa.me/{RESTAURANT_PROFILE['whatsapp_number']}?text={quote(message)}"


def _table_exists(cursor, table_name):
    cursor.execute(
        """
        SELECT 1
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
        LIMIT 1
        """,
        (table_name,),
    )
    return cursor.fetchone() is not None


def _column_exists(cursor, table_name, column_name):
    cursor.execute(
        """
        SELECT 1
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND COLUMN_NAME = %s
        LIMIT 1
        """,
        (table_name, column_name),
    )
    return cursor.fetchone() is not None


def get_nila_size_price_map(cursor):
    if not _table_exists(cursor, "fish_size_prices"):
        return {}

    cursor.execute(
        """
        SELECT size_category, price
        FROM fish_size_prices
        WHERE price IS NOT NULL
        """
    )
    return {
        str(row.get("size_category") or "").strip(): int(row.get("price") or 0)
        for row in cursor.fetchall()
        if row.get("size_category")
    }


def ensure_public_booking_tables(cursor):
    ensure_additional_stock_tables(cursor)

    if _table_exists(cursor, "reservations"):
        reservation_columns = {
            "whatsapp_number": "ALTER TABLE reservations ADD COLUMN whatsapp_number VARCHAR(30) NULL AFTER customer_name",
            "booking_end_datetime": "ALTER TABLE reservations ADD COLUMN booking_end_datetime DATETIME NULL AFTER reservation_datetime",
            "booking_source": "ALTER TABLE reservations ADD COLUMN booking_source VARCHAR(40) NOT NULL DEFAULT 'panel' AFTER booking_end_datetime",
            "booking_area": "ALTER TABLE reservations ADD COLUMN booking_area VARCHAR(80) NULL AFTER booking_source",
            "booking_resource_code": "ALTER TABLE reservations ADD COLUMN booking_resource_code VARCHAR(80) NULL AFTER booking_area",
            "booking_resource_codes": "ALTER TABLE reservations ADD COLUMN booking_resource_codes TEXT NULL AFTER booking_resource_code",
            "booking_setup": "ALTER TABLE reservations ADD COLUMN booking_setup VARCHAR(80) NULL AFTER booking_resource_code",
        }
        for column_name, sql in reservation_columns.items():
            if not _column_exists(cursor, "reservations", column_name):
                cursor.execute(sql)
        cursor.execute("ALTER TABLE reservations MODIFY COLUMN table_number VARCHAR(255) NULL")

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS booking_resources (
            id INT AUTO_INCREMENT PRIMARY KEY,
            resource_code VARCHAR(80) NOT NULL,
            area_name VARCHAR(80) NOT NULL,
            resource_type ENUM('table','vip_setup') NOT NULL DEFAULT 'table',
            display_name VARCHAR(120) NOT NULL,
            table_label VARCHAR(50) NULL,
            seat_capacity INT NOT NULL DEFAULT 0,
            setup_key VARCHAR(80) NULL,
            image_url TEXT NULL,
            description TEXT NULL,
            is_active TINYINT(1) NOT NULL DEFAULT 1,
            sort_order INT NOT NULL DEFAULT 0,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY uq_booking_resources_code (resource_code)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        """
    )

    cursor.execute(
        """
        UPDATE booking_resources
        SET
            area_name = %s,
            display_name = 'VIP 1 Ala Carte - Classroom',
            seat_capacity = 50,
            setup_key = 'classroom',
            description = 'Layanan ala carte dengan setup classroom. Maksimal 50 tamu.',
            sort_order = 200
        WHERE resource_code = 'vip-classroom'
        """
        ,
        (BOOKING_VIP_AREA,)
    )
    cursor.execute(
        """
        UPDATE booking_resources
        SET
            area_name = %s,
            display_name = 'VIP 1 Ala Carte - Meja Makan',
            seat_capacity = 50,
            setup_key = 'dining_table',
            description = 'Layanan ala carte dengan setup meja makan. Maksimal 50 tamu.',
            sort_order = 220
        WHERE resource_code = 'vip-dining-table'
        """
        ,
        (BOOKING_VIP_AREA,)
    )
    cursor.execute(
        """
        UPDATE booking_resources
        SET
            area_name = %s,
            display_name = 'VIP 1 Prasmanan',
            seat_capacity = 50,
            setup_key = 'prasmanan',
            description = 'Layanan VIP 1 prasmanan. Cocok untuk acara privat dengan maksimal 50 tamu.',
            sort_order = 230
        WHERE resource_code = 'vip-prasmanan'
        """
        ,
        (BOOKING_VIP_AREA,)
    )
    cursor.execute(
        """
        UPDATE booking_resources
        SET
            area_name = %s,
            display_name = 'VIP 1 Ala Carte - Letter U',
            seat_capacity = 50,
            setup_key = 'letter_u',
            description = 'Layanan ala carte dengan setup Letter U. Maksimal 50 tamu.',
            sort_order = 210
        WHERE resource_code = 'vip-letter-u'
        """
        ,
        (BOOKING_VIP_AREA,)
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS menu_display_assets (
            menu_id INT NOT NULL,
            image_url TEXT NULL,
            short_description VARCHAR(255) NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (menu_id),
            CONSTRAINT fk_menu_display_assets_menu
                FOREIGN KEY (menu_id) REFERENCES menus(id)
                ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        """
    )

    for resource in DEFAULT_BOOKING_RESOURCES:
        cursor.execute(
            """
            INSERT INTO booking_resources (
                resource_code, area_name, resource_type, display_name, table_label,
                seat_capacity, setup_key, image_url, description, sort_order
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
                area_name = VALUES(area_name),
                resource_type = VALUES(resource_type),
                display_name = VALUES(display_name),
                table_label = VALUES(table_label),
                seat_capacity = VALUES(seat_capacity),
                setup_key = VALUES(setup_key),
                image_url = CASE
                    WHEN COALESCE(image_url, '') = '' THEN VALUES(image_url)
                    ELSE image_url
                END,
                description = VALUES(description),
                sort_order = VALUES(sort_order)
            """,
            (
                resource["resource_code"],
                resource["area_name"],
                resource["resource_type"],
                resource["display_name"],
                resource["table_label"],
                resource["seat_capacity"],
                resource["setup_key"],
                resource.get("image_url"),
                resource["description"],
                resource["sort_order"],
            ),
        )


def normalize_whatsapp_number(value):
    digits = re.sub(r"\D+", "", (value or "").strip())
    if digits.startswith("62") or not digits:
        return digits
    if digits.startswith("0"):
        return digits
    return digits


def get_default_booking_end(start_datetime):
    return start_datetime + timedelta(hours=DEFAULT_BOOKING_DURATION_HOURS)


def resolve_booking_end(start_datetime, end_datetime=None):
    return end_datetime or get_default_booking_end(start_datetime)


def normalize_booking_area_name(area_name):
    area_name = (area_name or "").strip()
    normalized = normalize_text(area_name)
    if normalized == "vip":
        return BOOKING_VIP_AREA
    return area_name


def is_area_allowed_for_guest_count(area_name, people_count):
    area_name = normalize_booking_area_name(area_name)
    if int(people_count or 0) > VIP_MAX_GUESTS:
        return area_name in LARGE_PARTY_ALLOWED_AREAS
    return True


def is_vip_area(area_name):
    return normalize_text(normalize_booking_area_name(area_name)).startswith("vip")


def is_main_table_area(area_name):
    return normalize_text(normalize_booking_area_name(area_name)) == normalize_text(BOOKING_TABLE_AREA)


def build_guest_booking_rules():
    return {
        "vip_max_guests": VIP_MAX_GUESTS,
        "large_party_allowed_areas": LARGE_PARTY_ALLOWED_AREAS,
        "large_party_blocked_areas": LARGE_PARTY_BLOCKED_AREAS,
        "large_party_message": "Untuk jumlah tamu lebih dari 50 orang, sistem hanya merekomendasikan Hall, Outdoor, atau Ruang Utama. Area VIP dan Kanopi tidak tersedia.",
    }


def get_resource_service_mode(resource_row):
    area_name = str((resource_row or {}).get("area_name") or "")
    resource_code = str((resource_row or {}).get("resource_code") or "")
    setup_key = str((resource_row or {}).get("setup_key") or "")
    if not is_vip_area(area_name):
        return ""
    if "prasmanan" in resource_code or setup_key == "prasmanan":
        return "prasmanan"
    return "alacarte"


def get_resource_service_mode_label(resource_row):
    mode = get_resource_service_mode(resource_row)
    if mode == "prasmanan":
        return "Prasmanan"
    if mode == "alacarte":
        return "Ala Carte"
    return ""


def format_datetime_input(value):
    if not value:
        return ""
    if isinstance(value, str):
        return value
    return value.strftime("%Y-%m-%dT%H:%M")


def parse_resource_codes_value(value):
    raw_value = (value or "").strip()
    if not raw_value:
        return []
    try:
        parsed = json.loads(raw_value)
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]
    except (TypeError, ValueError, json.JSONDecodeError):
        pass
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def serialize_resource_selection(resource_rows, extra_chairs=0):
    rows = list(resource_rows or [])
    if not rows:
        return "BOOKING-WEB"

    area_name = normalize_booking_area_name(rows[0].get("area_name") or "")
    if is_main_table_area(area_name):
        table_labels = [str(row.get("table_label") or "").strip() for row in rows if str(row.get("table_label") or "").strip()]
        label = f"{area_name} - Meja {', '.join(table_labels)}" if table_labels else area_name
        if int(extra_chairs or 0) > 0:
            label += f" (+{int(extra_chairs)} kursi tambahan)"
        return label

    resource = rows[0]
    return resource.get("display_name") or area_name or "BOOKING-WEB"


def format_datetime_display(value):
    if not value:
        return "-"
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return value
    return value.strftime("%d %b %Y %H:%M")


def describe_booking_resource(row):
    if not row:
        return "-"

    display_name = (row.get("display_name") or "").strip()
    area_name = (row.get("area_name") or "").strip()
    seat_capacity = int(row.get("seat_capacity") or 0)

    parts = [display_name or area_name or "-"]
    if seat_capacity > 0:
        parts.append(f"{seat_capacity} kursi")
    return " | ".join(parts)


def build_public_booking_description(whatsapp_number, seating_preference, notes, selected_menus=None):
    parts = ["Sumber: Website Booking"]

    if whatsapp_number:
        parts.append(f"WhatsApp: {whatsapp_number}")

    if seating_preference:
        parts.append(f"Preferensi: {seating_preference}")

    if selected_menus:
        parts.append(f"Menu dipilih: {selected_menus}")

    if notes:
        parts.append(f"Catatan: {notes}")

    return " | ".join(parts)


def get_menu_media_map(cursor):
    ensure_public_booking_tables(cursor)
    cursor.execute(
        """
        SELECT menu_id, image_url, short_description
        FROM menu_display_assets
        """
    )
    return {row["menu_id"]: row for row in cursor.fetchall()}


def get_menu_media_rows(cursor):
    ensure_public_booking_tables(cursor)
    cursor.execute(
        """
        SELECT
            m.id,
            m.name,
            m.category,
            m.serving_type,
            m.price,
            m.divisi,
            COALESCE(a.image_url, '') AS image_url,
            COALESCE(a.short_description, '') AS short_description
        FROM menus m
        LEFT JOIN menu_display_assets a ON a.menu_id = m.id
        ORDER BY m.name, m.id
        """
    )
    rows = cursor.fetchall()
    for row in rows:
        row["price_display"] = format_currency(row.get("price"))
        row["menu_label"] = format_menu_label(row.get("name"), row.get("serving_type"))
    return rows


def get_booking_resources(cursor):
    ensure_public_booking_tables(cursor)
    cursor.execute(
        """
        SELECT
            id,
            resource_code,
            area_name,
            resource_type,
            display_name,
            table_label,
            seat_capacity,
            setup_key,
            COALESCE(image_url, '') AS image_url,
            COALESCE(description, '') AS description,
            is_active,
            sort_order
        FROM booking_resources
        ORDER BY area_name, sort_order, display_name
        """
    )
    return cursor.fetchall()


def get_booking_resource_map(cursor):
    return {row["resource_code"]: row for row in get_booking_resources(cursor)}


def _preview_menu_id(menu):
    menu_id = menu.get("menu_id")
    if menu_id is not None:
        return int(menu_id)

    combo_map = menu.get("combo_map") or {}
    for combo in combo_map.values():
        combo_menu_id = combo.get("menu_id")
        if combo_menu_id is not None:
            return int(combo_menu_id)
    return None


def _default_menu_description(menu):
    category = (menu.get("category") or "").replace("_", " ").title()
    divisi = (menu.get("divisi") or "").replace("_", " ").title()
    stock_source = (menu.get("stock_source") or menu.get("stock_type") or "").replace("_", " ")
    parts = [part for part in [category, divisi, stock_source] if part]
    if not parts:
        return "Pilihan menu tersedia sesuai update stok harian."
    return " • ".join(parts)


def _build_stock_hint_text(menu, nila_sizes, sea_fish, rahang_tuna_stock):
    stock_source = (menu.get("stock_source") or menu.get("stock_type") or "").strip().lower()

    if stock_source == "size":
        labels = [row.get("label") or format_size_category_label(row.get("size_category")) for row in nila_sizes if row.get("size_category")]
        if labels:
            return f"Size tersedia: {', '.join(labels)}."
        return "Size nila mengikuti update stock terbaru."

    if stock_source == "weight":
        labels = [row.get("label") or row.get("display_weight") for row in sea_fish if row.get("display_weight")]
        if labels:
            return f"Berat ikan tersedia: {', '.join(labels[:4])}."
        return "Berat ikan laut mengikuti update stock terbaru."

    if stock_source == "tuna_weight":
        labels = [row.get("label") or row.get("display_weight") for row in rahang_tuna_stock.get("rows", []) if row.get("display_weight")]
        if labels:
            return f"Berat rahang tersedia: {', '.join(labels[:4])}."
        return "Berat rahang tuna mengikuti update stock terbaru."

    return ""


def _build_item_selection_detail(item):
    fish_size = (item.get("fish_size") or "").strip()
    if fish_size:
        return f"Size {format_size_category_label(fish_size)}"

    fish_type = (item.get("fish_type") or "").strip()
    fish_weight = item.get("fish_weight")

    if fish_weight not in (None, "", "0", "0.0"):
        weight_label = format_weight_display(fish_weight)
        if fish_type.lower() == "rahang tuna":
            return f"Rahang Tuna {weight_label}"
        if fish_type:
            return f"{fish_type.title()} {weight_label}"
        return weight_label

    return ""


def _resolve_public_menu_group(menu):
    category = normalize_text(menu.get("category"))
    divisi = normalize_text(menu.get("divisi"))
    name = normalize_text(menu.get("name"))

    if category == "ayam":
        return PUBLIC_MENU_GROUP_LOOKUP["ayam"]
    if category == "ikan nila":
        return PUBLIC_MENU_GROUP_LOOKUP["ikan_nila"]
    if category in {"ikan laut", "ikan tuna", "udang", "cumi"}:
        return PUBLIC_MENU_GROUP_LOOKUP["seafood"]
    if category == "daging":
        return PUBLIC_MENU_GROUP_LOOKUP["daging"]
    if category == "side":
        return PUBLIC_MENU_GROUP_LOOKUP["menu_sampingan"]
    if category in {"soup", "sayuran"}:
        return PUBLIC_MENU_GROUP_LOOKUP["soup_sayur"]
    if category in {"nasi", "mie"} or "bubur" in name:
        return PUBLIC_MENU_GROUP_LOOKUP["nasi_mie_bubur"]
    if category == "chilin" or divisi == "taiwan snack" or "taiwan" in divisi:
        return PUBLIC_MENU_GROUP_LOOKUP["taiwan_dish"]
    if category == "snack":
        return PUBLIC_MENU_GROUP_LOOKUP["snack"]
    if category == "dessert":
        return PUBLIC_MENU_GROUP_LOOKUP["dessert"]
    if category == "nokoffie":
        return PUBLIC_MENU_GROUP_LOOKUP["non_koffie"]
    if category in {"drink", "koffie"}:
        return PUBLIC_MENU_GROUP_LOOKUP["minuman_koffie"]
    if divisi == "bar":
        return PUBLIC_MENU_GROUP_LOOKUP["minuman_koffie"]
    return {"key": "lainnya", "label": "Menu Lainnya", "order": 999}


def prepare_public_menu_catalog(cursor, selected_date):
    ensure_public_booking_tables(cursor)
    menu_catalog, nila_sizes, sea_fish = get_stock_context(cursor, selected_date)
    _, tuna_piece_stock, rahang_tuna_stock = get_special_tuna_stock_context(cursor, selected_date)
    nila_size_price_map = get_nila_size_price_map(cursor)
    media_map = get_menu_media_map(cursor)

    prepared_catalog = []
    for raw_menu in menu_catalog:
        menu = dict(raw_menu)
        preview_menu_id = _preview_menu_id(menu)
        media_row = media_map.get(preview_menu_id, {})
        group_info = _resolve_public_menu_group(menu)
        menu["preview_menu_id"] = preview_menu_id
        menu["price_display"] = format_currency(menu.get("price"))
        menu["image_url"] = media_row.get("image_url") or ""
        menu["short_description"] = (media_row.get("short_description") or "").strip() or _default_menu_description(menu)
        menu["display_label"] = format_menu_label(menu.get("name"), menu.get("serving_type"))
        menu["public_group_key"] = group_info["key"]
        menu["public_group_label"] = group_info["label"]
        menu["public_group_order"] = group_info["order"]
        if (menu.get("stock_source") or menu.get("stock_type")) == "size":
            menu["size_price_map"] = nila_size_price_map
            available_size_prices = [
                nila_size_price_map.get(row.get("size_category"))
                for row in nila_sizes
                if row.get("size_category") in nila_size_price_map
            ]
            available_size_prices = [price for price in available_size_prices if price is not None]
            if available_size_prices:
                menu["size_price_min"] = min(available_size_prices)
                menu["size_price_min_display"] = format_currency(menu["size_price_min"])
        prepared_catalog.append(menu)

    for fish in sea_fish:
        fish["display_weight"] = format_weight_display(fish.get("weight_ons"), fish.get("weight_unit"))
        fish["label"] = f"{fish.get('name', 'Ikan').capitalize()} - {fish['display_weight']}"

    for row in rahang_tuna_stock.get("rows", []):
        row["display_weight"] = format_weight_display(row.get("weight_ons"), row.get("weight_unit"))
        row["label"] = f"Rahang Tuna - {row['display_weight']}"

    for menu in prepared_catalog:
        menu["stock_hint"] = _build_stock_hint_text(menu, nila_sizes, sea_fish, rahang_tuna_stock)

    prepared_catalog.sort(
        key=lambda item: (
            int(item.get("public_group_order") or 999),
            normalize_text(item.get("display_label") or item.get("name")),
        )
    )

    return prepared_catalog, nila_sizes, sea_fish, tuna_piece_stock, rahang_tuna_stock


def get_booked_resource_codes(cursor, start_datetime, end_datetime, exclude_reservation_id=None):
    ensure_public_booking_tables(cursor)
    query = """
        SELECT booking_resource_code, booking_resource_codes
        FROM reservations
        WHERE (
                (booking_resource_code IS NOT NULL AND booking_resource_code <> '')
             OR (booking_resource_codes IS NOT NULL AND booking_resource_codes <> '')
              )
          AND reservation_datetime < %s
          AND COALESCE(booking_end_datetime, DATE_ADD(reservation_datetime, INTERVAL %s HOUR)) > %s
    """
    params = [end_datetime, DEFAULT_BOOKING_DURATION_HOURS, start_datetime]

    if exclude_reservation_id:
        query += " AND id <> %s"
        params.append(exclude_reservation_id)

    cursor.execute(query, tuple(params))
    booked_codes = set()
    for row in cursor.fetchall():
        booked_codes.update(parse_resource_codes_value(row.get("booking_resource_codes")))
        if row.get("booking_resource_code"):
            booked_codes.add(str(row.get("booking_resource_code")).strip())
    return {code for code in booked_codes if code}


def build_booking_resource_sections(cursor, start_datetime, end_datetime, exclude_reservation_id=None):
    resource_rows = get_booking_resources(cursor)
    booked_codes = get_booked_resource_codes(cursor, start_datetime, end_datetime, exclude_reservation_id=exclude_reservation_id)
    area_order = {
        BOOKING_TABLE_AREA: 10,
        BOOKING_VIP_AREA: 20,
        BOOKING_VIP_SECOND_AREA: 25,
        BOOKING_HALL_AREA: 30,
        BOOKING_OUTDOOR_AREA: 40,
        BOOKING_CANOPY_AREA: 50,
    }
    area_sections = OrderedDict()

    for row in resource_rows:
        item = dict(row)
        item["area_name"] = normalize_booking_area_name(item.get("area_name"))
        item["is_available"] = item["resource_code"] not in booked_codes
        item["capacity_label"] = f"{int(item.get('seat_capacity') or 0)} kursi" if int(item.get("seat_capacity") or 0) > 0 else "-"
        item["service_mode"] = get_resource_service_mode(item)
        item["service_mode_label"] = get_resource_service_mode_label(item)
        area_name = item.get("area_name") or "Lainnya"
        if area_name not in area_sections:
            area_sections[area_name] = {
                "area_name": area_name,
                "order": area_order.get(area_name, 999),
                "resources": [],
            }
        area_sections[area_name]["resources"].append(item)

    ordered_sections = sorted(area_sections.values(), key=lambda row: (row["order"], row["area_name"]))

    return {
        "main_tables": [item for section in ordered_sections if section["area_name"] == BOOKING_TABLE_AREA for item in section["resources"]],
        "vip_layouts": [item for section in ordered_sections if section["area_name"] == BOOKING_VIP_AREA for item in section["resources"]],
        "area_sections": ordered_sections,
        "booked_codes": sorted(booked_codes),
    }


def build_public_availability_payload(cursor, start_datetime, end_datetime, exclude_reservation_id=None):
    sections = build_booking_resource_sections(cursor, start_datetime, end_datetime, exclude_reservation_id=exclude_reservation_id)
    return {
        "main_tables": [
            {
                "resource_code": row["resource_code"],
                "area_name": row.get("area_name"),
                "display_name": row["display_name"],
                "table_label": row.get("table_label"),
                "seat_capacity": row.get("seat_capacity"),
                "capacity_label": row.get("capacity_label"),
                "resource_type": row.get("resource_type"),
                "image_url": row.get("image_url"),
                "description": row.get("description"),
                "is_available": row["is_available"],
                "service_mode": row.get("service_mode"),
                "service_mode_label": row.get("service_mode_label"),
            }
            for row in sections["main_tables"]
        ],
        "vip_layouts": [
            {
                "resource_code": row["resource_code"],
                "area_name": row.get("area_name"),
                "display_name": row["display_name"],
                "setup_key": row.get("setup_key"),
                "seat_capacity": row.get("seat_capacity"),
                "capacity_label": row.get("capacity_label"),
                "resource_type": row.get("resource_type"),
                "image_url": row.get("image_url"),
                "description": row.get("description"),
                "is_available": row["is_available"],
                "service_mode": row.get("service_mode"),
                "service_mode_label": row.get("service_mode_label"),
            }
            for row in sections["vip_layouts"]
        ],
        "area_sections": [
            {
                "area_name": section["area_name"],
                "resources": [
                    {
                        "resource_code": row["resource_code"],
                        "area_name": row.get("area_name"),
                        "display_name": row["display_name"],
                        "table_label": row.get("table_label"),
                        "setup_key": row.get("setup_key"),
                        "seat_capacity": row.get("seat_capacity"),
                        "capacity_label": row.get("capacity_label"),
                        "resource_type": row.get("resource_type"),
                        "image_url": row.get("image_url"),
                        "description": row.get("description"),
                        "is_available": row["is_available"],
                        "service_mode": row.get("service_mode"),
                        "service_mode_label": row.get("service_mode_label"),
                    }
                    for row in section["resources"]
                ],
            }
            for section in sections["area_sections"]
        ],
        "booked_codes": sections["booked_codes"],
    }


def build_selected_menu_summary(items, menu_catalog):
    menu_lookup = {str(menu.get("id")): menu for menu in menu_catalog}
    summary_parts = []
    for item in items:
        qty = int(item.get("qty") or 0)
        if qty <= 0:
            continue
        menu = menu_lookup.get(str(item.get("display_menu_id")))
        label = (menu or {}).get("display_label") or (menu or {}).get("name") or "Menu"
        detail = _build_item_selection_detail(item)
        if detail:
            label = f"{label} ({detail})"
        summary_parts.append(f"{label} x{qty}")
    return ", ".join(summary_parts[:6])


def parse_booking_items(raw_payload):
    if not raw_payload:
        return []

    try:
        items = json.loads(raw_payload)
    except (TypeError, ValueError):
        raise ValueError("Data menu booking tidak valid.")

    if not isinstance(items, list):
        raise ValueError("Format data menu booking tidak dikenali.")

    normalized_items = []
    for item in items:
        if not isinstance(item, dict):
            continue
        normalized_items.append(
            {
                "display_menu_id": str(item.get("display_menu_id") or "").strip(),
                "menu_id": str(item.get("menu_id") or "").strip(),
                "qty": int(item.get("qty") or 0),
                "menu_options_json": item.get("menu_options_json") or None,
                "fish_type": (item.get("fish_type") or "").strip() or None,
                "fish_size": (item.get("fish_size") or "").strip() or None,
                "fish_weight": item.get("fish_weight") or None,
                "fish_stock_id": item.get("fish_stock_id") or None,
                "special_stock_id": item.get("special_stock_id") or None,
                "special_request": _normalize_special_request_value(item.get("special_request")),
                "dish_description": (item.get("dish_description") or "").strip() or None,
            }
        )
    return [item for item in normalized_items if item["qty"] > 0 and item["display_menu_id"]]


def _normalize_special_request_value(raw_value):
    value = str(raw_value or "").strip().lower()
    return "with_special" if value in {"with_special", "special_request"} else "no_special"


def persist_public_booking_items(cursor, reservation_id, reservation_date, raw_payload):
    items = parse_booking_items(raw_payload)
    if not items:
        return []

    menu_catalog, _, _ = get_stock_context(cursor, reservation_date)
    created_items = []

    for item in items:
        resolved_menu_id = resolve_menu_submission(
            menu_catalog,
            item.get("menu_id"),
            display_menu_id=item.get("display_menu_id"),
            menu_options_json=item.get("menu_options_json"),
        )
        if resolved_menu_id is None:
            raise ValueError("Ada menu booking yang tidak valid. Silakan pilih ulang menu Anda.")

        fish_type = item.get("fish_type")
        fish_size = item.get("fish_size")
        fish_weight = item.get("fish_weight")
        special_request_value = _normalize_special_request_value(item.get("special_request"))
        dish_description = (item.get("dish_description") or "").strip() or None

        resolved_fish_stock_id, resolved_special_stock_id = resolve_selected_stock_refs(
            cursor,
            reservation_date,
            resolved_menu_id,
            fish_type=fish_type,
            fish_weight=fish_weight,
            fish_stock_id=item.get("fish_stock_id"),
            special_stock_id=item.get("special_stock_id"),
        )

        is_valid_stock, stock_message = validate_stock_request(
            cursor,
            reservation_date,
            resolved_menu_id,
            item.get("qty"),
            fish_type=fish_type,
            fish_size=fish_size,
            fish_weight=fish_weight,
            fish_stock_id=resolved_fish_stock_id,
            special_stock_id=resolved_special_stock_id,
            menu_options_json=item.get("menu_options_json"),
        )
        if not is_valid_stock:
            raise ValueError(stock_message)

        cursor.execute(
            """
            INSERT INTO reservation_items (
                reservation_id, menu_id, quantity, special_request, dish_description,
                fish_type, fish_size, fish_weight, fish_stock_ref_id, special_stock_ref_id, menu_options_json
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                reservation_id,
                resolved_menu_id,
                item.get("qty"),
                special_request_value,
                dish_description,
                fish_type,
                fish_size,
                fish_weight,
                resolved_fish_stock_id,
                resolved_special_stock_id,
                item.get("menu_options_json") or None,
            ),
        )

        reduce_stock_after_order(
            cursor,
            fish_stock_id=resolved_fish_stock_id,
            special_stock_id=resolved_special_stock_id,
            qty=int(item.get("qty") or 0),
        )

        created_items.append(
            {
                "menu_id": resolved_menu_id,
                "qty": int(item.get("qty") or 0),
                "display_menu_id": item.get("display_menu_id"),
            }
        )

    return created_items


def get_reservation_end_datetime(row):
    reservation_datetime = row.get("reservation_datetime")
    booking_end_datetime = row.get("booking_end_datetime")

    if not reservation_datetime:
        return None

    if booking_end_datetime:
        return booking_end_datetime

    if isinstance(reservation_datetime, str):
        try:
            reservation_datetime = datetime.strptime(reservation_datetime, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None

    return reservation_datetime + timedelta(hours=DEFAULT_BOOKING_DURATION_HOURS)


def build_booking_summary(row):
    parts = []
    whatsapp_number = (row.get("whatsapp_number") or "").strip()
    booking_area = normalize_booking_area_name(row.get("booking_area"))
    booking_setup = (row.get("booking_setup") or "").strip()
    booking_end_datetime = get_reservation_end_datetime(row)

    if whatsapp_number:
        parts.append(f"WA {whatsapp_number}")
    if booking_area:
        parts.append(booking_area)
    if booking_setup:
        parts.append(booking_setup.replace("_", " ").title())
    if booking_end_datetime:
        parts.append(f"sampai {format_datetime_display(booking_end_datetime)}")
    return " | ".join(parts)


def serialize_resource_label(resource_row):
    if not resource_row:
        return "BOOKING-WEB"
    return serialize_resource_selection([resource_row])
