import json
import re
from datetime import date, datetime, time, timedelta

from services.history import build_menu_history_summary, get_menu_label_for_history, log_reservation_history
from services.menu_options import build_menu_display_note, resolve_menu_submission
from services.public_booking import (
    BOOKING_TABLE_AREA,
    DEFAULT_BOOKING_DURATION_HOURS,
    ensure_public_booking_tables,
    parse_resource_codes_value,
    serialize_resource_selection,
)
from services.stock import (
    get_stock_context,
    reduce_stock_after_order,
    resolve_selected_stock_refs,
    validate_stock_request,
)


DEFAULT_RESERVATION_DURATION_MINUTES = DEFAULT_BOOKING_DURATION_HOURS * 60
RESERVATION_BLOCKING_STATUSES = {"pending", "confirmed", "occupied"}
ACTIVE_OCCUPANCY_STATUSES = {"occupied"}
NON_BLOCKING_RESERVATION_STATUSES = {"cancelled", "completed"}

TAIWAN_SEASONING_CHOICES = [
    {"value": "balado", "label": "Balado"},
    {"value": "keju", "label": "Keju"},
    {"value": "bbq", "label": "BBQ"},
    {"value": "jagung_bakar", "label": "Jagung Bakar"},
    {"value": "sapi_panggang", "label": "Sapi Panggang"},
    {"value": "extra_hot", "label": "Extra Hot"},
]

MAIN_ROOM_FLOOR_TABLES = [
    {
        "resource_code": "main-01",
        "name": "Meja 1",
        "table_label": "1",
        "area": BOOKING_TABLE_AREA,
        "sub_zone": "Upper AC Row",
        "shape": "round_rect",
        "x_position": 540,
        "y_position": 96,
        "width": 68,
        "height": 32,
        "radius": 10,
        "capacity": 4,
        "sort_order": 10,
        "description": "Baris atas paling kanan, dekat wastafel dan toilet.",
    },
    {
        "resource_code": "main-02",
        "name": "Meja 2",
        "table_label": "2",
        "area": BOOKING_TABLE_AREA,
        "sub_zone": "Upper AC Row",
        "shape": "round_rect",
        "x_position": 452,
        "y_position": 96,
        "width": 68,
        "height": 32,
        "radius": 10,
        "capacity": 4,
        "sort_order": 20,
        "description": "Baris atas dekat AC.",
    },
    {
        "resource_code": "main-03",
        "name": "Meja 3",
        "table_label": "3",
        "area": BOOKING_TABLE_AREA,
        "sub_zone": "Upper AC Row",
        "shape": "round_rect",
        "x_position": 364,
        "y_position": 96,
        "width": 68,
        "height": 32,
        "radius": 10,
        "capacity": 4,
        "sort_order": 30,
        "description": "Baris atas dekat AC dan panggung live music.",
    },
    {
        "resource_code": "main-04",
        "name": "Meja 4",
        "table_label": "4",
        "area": BOOKING_TABLE_AREA,
        "sub_zone": "Upper AC Row",
        "shape": "round_rect",
        "x_position": 276,
        "y_position": 96,
        "width": 68,
        "height": 32,
        "radius": 10,
        "capacity": 4,
        "sort_order": 40,
        "description": "Baris atas paling kiri dekat panggung live music.",
    },
    {
        "resource_code": "main-11a",
        "name": "Meja 11",
        "table_label": "11",
        "area": BOOKING_TABLE_AREA,
        "sub_zone": "Left Window Column",
        "shape": "round_rect",
        "x_position": 164,
        "y_position": 558,
        "width": 54,
        "height": 78,
        "radius": 16,
        "capacity": 2,
        "sort_order": 50,
        "description": "Meja dua kursi paling bawah dekat jendela sisi kiri.",
    },
    {
        "resource_code": "main-11b",
        "name": "Meja 11B",
        "table_label": "11B",
        "area": BOOKING_TABLE_AREA,
        "sub_zone": "Left Window Column",
        "shape": "round_rect",
        "x_position": 164,
        "y_position": 470,
        "width": 54,
        "height": 78,
        "radius": 16,
        "capacity": 2,
        "sort_order": 60,
        "description": "Meja dua kursi dekat jendela sisi kiri.",
    },
    {
        "resource_code": "main-12a",
        "name": "Meja 12",
        "table_label": "12",
        "area": BOOKING_TABLE_AREA,
        "sub_zone": "Left Window Column",
        "shape": "round_rect",
        "x_position": 164,
        "y_position": 294,
        "width": 54,
        "height": 78,
        "radius": 16,
        "capacity": 2,
        "sort_order": 70,
        "description": "Meja dua kursi paling dekat pintu masuk dan jendela.",
    },
    {
        "resource_code": "main-12b",
        "name": "Meja 12B",
        "table_label": "12B",
        "area": BOOKING_TABLE_AREA,
        "sub_zone": "Left Window Column",
        "shape": "round_rect",
        "x_position": 164,
        "y_position": 382,
        "width": 54,
        "height": 78,
        "radius": 16,
        "capacity": 2,
        "sort_order": 80,
        "description": "Meja dua kursi di bawah Meja 12 dekat jendela.",
    },
    {
        "resource_code": "main-05",
        "name": "Meja 5",
        "table_label": "5",
        "area": BOOKING_TABLE_AREA,
        "sub_zone": "Upper Center Row",
        "shape": "round_rect",
        "x_position": 540,
        "y_position": 184,
        "width": 68,
        "height": 32,
        "radius": 10,
        "capacity": 4,
        "sort_order": 90,
        "description": "Persis di bawah Meja 1.",
    },
    {
        "resource_code": "main-05b",
        "name": "Meja 5B",
        "table_label": "5B",
        "area": BOOKING_TABLE_AREA,
        "sub_zone": "Upper Center Row",
        "shape": "round_rect",
        "x_position": 452,
        "y_position": 184,
        "width": 68,
        "height": 32,
        "radius": 10,
        "capacity": 4,
        "sort_order": 100,
        "description": "Persis di bawah Meja 2.",
    },
    {
        "resource_code": "main-06",
        "name": "Meja 6",
        "table_label": "6",
        "area": BOOKING_TABLE_AREA,
        "sub_zone": "Upper Center Row",
        "shape": "round_rect",
        "x_position": 276,
        "y_position": 184,
        "width": 68,
        "height": 32,
        "radius": 10,
        "capacity": 4,
        "sort_order": 110,
        "description": "Persis di bawah Meja 4.",
    },
    {
        "resource_code": "main-06b",
        "name": "Meja 6B",
        "table_label": "6B",
        "area": BOOKING_TABLE_AREA,
        "sub_zone": "Upper Center Row",
        "shape": "round_rect",
        "x_position": 364,
        "y_position": 184,
        "width": 68,
        "height": 32,
        "radius": 10,
        "capacity": 4,
        "sort_order": 120,
        "description": "Persis di bawah Meja 3.",
    },
    {
        "resource_code": "main-07",
        "name": "Meja 7",
        "table_label": "7",
        "area": BOOKING_TABLE_AREA,
        "sub_zone": "Middle Right Column",
        "shape": "round_rect",
        "x_position": 420,
        "y_position": 300,
        "width": 58,
        "height": 86,
        "radius": 16,
        "capacity": 4,
        "sort_order": 130,
        "description": "Kolom tengah kanan bagian atas.",
    },
    {
        "resource_code": "main-08",
        "name": "Meja 8",
        "table_label": "8",
        "area": BOOKING_TABLE_AREA,
        "sub_zone": "Middle Right Column",
        "shape": "round_rect",
        "x_position": 420,
        "y_position": 500,
        "width": 58,
        "height": 86,
        "radius": 16,
        "capacity": 4,
        "sort_order": 140,
        "description": "Kolom tengah kanan bagian bawah.",
    },
    {
        "resource_code": "main-08b",
        "name": "Meja 8B",
        "table_label": "8B",
        "area": BOOKING_TABLE_AREA,
        "sub_zone": "Middle Right Column",
        "shape": "round_rect",
        "x_position": 420,
        "y_position": 400,
        "width": 58,
        "height": 86,
        "radius": 16,
        "capacity": 4,
        "sort_order": 150,
        "description": "Kolom tengah kanan bagian tengah.",
    },
    {
        "resource_code": "main-09",
        "name": "Meja 9",
        "table_label": "9",
        "area": BOOKING_TABLE_AREA,
        "sub_zone": "Middle Left Column",
        "shape": "round_rect",
        "x_position": 230,
        "y_position": 500,
        "width": 58,
        "height": 86,
        "radius": 16,
        "capacity": 4,
        "sort_order": 160,
        "description": "Kolom tengah kiri bagian bawah.",
    },
    {
        "resource_code": "main-10",
        "name": "Meja 10",
        "table_label": "10",
        "area": BOOKING_TABLE_AREA,
        "sub_zone": "Middle Left Column",
        "shape": "round_rect",
        "x_position": 230,
        "y_position": 300,
        "width": 58,
        "height": 86,
        "radius": 16,
        "capacity": 4,
        "sort_order": 170,
        "description": "Kolom tengah kiri bagian atas.",
    },
    {
        "resource_code": "main-10b",
        "name": "Meja 10B",
        "table_label": "10B",
        "area": BOOKING_TABLE_AREA,
        "sub_zone": "Middle Left Column",
        "shape": "round_rect",
        "x_position": 230,
        "y_position": 400,
        "width": 58,
        "height": 86,
        "radius": 16,
        "capacity": 4,
        "sort_order": 180,
        "description": "Kolom tengah kiri bagian tengah.",
    },
]

RESOURCE_ALIAS_GROUPS = {
    "main-11": {"main-11", "main-11a", "main-11b"},
    "main-11a": {"main-11", "main-11a", "main-11b"},
    "main-11b": {"main-11", "main-11a", "main-11b"},
    "main-12": {"main-12", "main-12a", "main-12b"},
    "main-12a": {"main-12", "main-12a", "main-12b"},
    "main-12b": {"main-12", "main-12a", "main-12b"},
}

TABLE_CODE_BY_LABEL = {
    str(table["table_label"]).strip().lower(): table["resource_code"]
    for table in MAIN_ROOM_FLOOR_TABLES
}
TABLE_CODE_BY_LABEL["11"] = "main-11"
TABLE_CODE_BY_LABEL["12"] = "main-12"
TABLE_LABELS_BY_LENGTH = sorted(TABLE_CODE_BY_LABEL.keys(), key=len, reverse=True)


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


def _normalize_name(value):
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _table_codes_for_resource(resource_code):
    code = str(resource_code or "").strip().lower()
    if not code:
        return set()
    return set(RESOURCE_ALIAS_GROUPS.get(code, {code}))


def _status_severity(status_name):
    if status_name == "occupied":
        return 3
    if status_name == "reserved":
        return 2
    if status_name == "unavailable":
        return 1
    return 0


def _build_menu_feature_map():
    try:
        from services.menu_options import MENU_DISPLAY_GROUPS, MENU_SINGLE_OPTION_CONFIGS
    except Exception:
        return {}

    feature_map = {}
    for menu_name, config in MENU_SINGLE_OPTION_CONFIGS.items():
        feature_map[_normalize_name(menu_name)] = {
            "has_options": bool(config.get("option_groups")),
            "has_seasoning": any(group.get("key") == "seasoning" for group in config.get("option_groups", [])),
        }

    for group in MENU_DISPLAY_GROUPS:
        has_options = bool(group.get("option_groups"))
        has_seasoning = any(option_group.get("key") == "seasoning" for option_group in group.get("option_groups", []))
        for menu_name in group.get("match_names", []):
            feature_map[_normalize_name(menu_name)] = {
                "has_options": has_options,
                "has_seasoning": has_seasoning,
            }

    return feature_map


MENU_FEATURE_MAP = _build_menu_feature_map()


def ensure_reservation_floor_schema(cursor):
    ensure_public_booking_tables(cursor)

    if _table_exists(cursor, "reservations"):
        if not _column_exists(cursor, "reservations", "duration_minutes"):
            cursor.execute(
                """
                ALTER TABLE reservations
                ADD COLUMN duration_minutes INT NOT NULL DEFAULT 120 AFTER reservation_datetime
                """
            )

        if not _column_exists(cursor, "reservations", "status"):
            cursor.execute(
                """
                ALTER TABLE reservations
                ADD COLUMN status ENUM('pending','confirmed','occupied','completed','cancelled')
                NOT NULL DEFAULT 'confirmed' AFTER duration_minutes
                """
            )

        cursor.execute(
            """
            UPDATE reservations
            SET duration_minutes = %s
            WHERE duration_minutes IS NULL OR duration_minutes <= 0
            """,
            (DEFAULT_RESERVATION_DURATION_MINUTES,),
        )
        cursor.execute(
            """
            UPDATE reservations
            SET status = 'confirmed'
            WHERE status IS NULL OR TRIM(status) = ''
            """
        )

    if _table_exists(cursor, "menus"):
        if not _column_exists(cursor, "menus", "has_options"):
            cursor.execute(
                """
                ALTER TABLE menus
                ADD COLUMN has_options TINYINT(1) NOT NULL DEFAULT 0 AFTER price
                """
            )
        if not _column_exists(cursor, "menus", "has_seasoning"):
            cursor.execute(
                """
                ALTER TABLE menus
                ADD COLUMN has_seasoning TINYINT(1) NOT NULL DEFAULT 0 AFTER has_options
                """
            )
        if not _column_exists(cursor, "menus", "is_active"):
            cursor.execute(
                """
                ALTER TABLE menus
                ADD COLUMN is_active TINYINT(1) NOT NULL DEFAULT 1 AFTER has_seasoning
                """
            )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS restaurant_tables (
            id INT AUTO_INCREMENT PRIMARY KEY,
            resource_code VARCHAR(80) NOT NULL,
            name VARCHAR(120) NOT NULL,
            table_label VARCHAR(30) NOT NULL,
            area VARCHAR(80) NOT NULL,
            sub_zone VARCHAR(80) NULL,
            x_position DECIMAL(8,2) NOT NULL DEFAULT 0,
            y_position DECIMAL(8,2) NOT NULL DEFAULT 0,
            width DECIMAL(8,2) NOT NULL DEFAULT 0,
            height DECIMAL(8,2) NOT NULL DEFAULT 0,
            radius DECIMAL(8,2) NOT NULL DEFAULT 0,
            shape ENUM('rect','round_rect','circle') NOT NULL DEFAULT 'round_rect',
            capacity INT NOT NULL DEFAULT 0,
            description TEXT NULL,
            sort_order INT NOT NULL DEFAULT 0,
            is_active TINYINT(1) NOT NULL DEFAULT 1,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY uq_restaurant_tables_resource_code (resource_code)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        """
    )

    cursor.execute(
        """
        SELECT
            resource_code,
            name,
            table_label,
            area,
            sub_zone,
            x_position,
            y_position,
            width,
            height,
            radius,
            shape,
            capacity,
            COALESCE(description, '') AS description,
            sort_order,
            is_active
        FROM restaurant_tables
        """
    )
    existing_floor_rows = {str(row.get("resource_code")).strip(): row for row in cursor.fetchall()}

    cursor.execute(
        """
        SELECT
            resource_code,
            area_name,
            display_name,
            table_label,
            seat_capacity,
            COALESCE(description, '') AS description,
            sort_order,
            COALESCE(is_active, 1) AS is_active
        FROM booking_resources
        """
    )
    existing_booking_rows = {str(row.get("resource_code")).strip(): row for row in cursor.fetchall()}

    for table in MAIN_ROOM_FLOOR_TABLES:
        existing_floor = existing_floor_rows.get(table["resource_code"])
        if not existing_floor:
            cursor.execute(
                """
                INSERT INTO restaurant_tables (
                    resource_code, name, table_label, area, sub_zone,
                    x_position, y_position, width, height, radius,
                    shape, capacity, description, sort_order, is_active
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,1)
                """,
                (
                    table["resource_code"],
                    table["name"],
                    table["table_label"],
                    table["area"],
                    table["sub_zone"],
                    table["x_position"],
                    table["y_position"],
                    table["width"],
                    table["height"],
                    table["radius"],
                    table["shape"],
                    table["capacity"],
                    table["description"],
                    table["sort_order"],
                ),
            )
        else:
            floor_values = (
                table["name"],
                table["table_label"],
                table["area"],
                table["sub_zone"],
                table["x_position"],
                table["y_position"],
                table["width"],
                table["height"],
                table["radius"],
                table["shape"],
                table["capacity"],
                table["description"],
                table["sort_order"],
                table["resource_code"],
            )
            if (
                str(existing_floor.get("name") or "") != str(table["name"])
                or str(existing_floor.get("table_label") or "") != str(table["table_label"])
                or str(existing_floor.get("area") or "") != str(table["area"])
                or str(existing_floor.get("sub_zone") or "") != str(table["sub_zone"])
                or float(existing_floor.get("x_position") or 0) != float(table["x_position"])
                or float(existing_floor.get("y_position") or 0) != float(table["y_position"])
                or float(existing_floor.get("width") or 0) != float(table["width"])
                or float(existing_floor.get("height") or 0) != float(table["height"])
                or float(existing_floor.get("radius") or 0) != float(table["radius"])
                or str(existing_floor.get("shape") or "") != str(table["shape"])
                or int(existing_floor.get("capacity") or 0) != int(table["capacity"])
                or str(existing_floor.get("description") or "") != str(table["description"] or "")
                or int(existing_floor.get("sort_order") or 0) != int(table["sort_order"])
                or int(existing_floor.get("is_active") or 0) != 1
            ):
                cursor.execute(
                    """
                    UPDATE restaurant_tables
                    SET
                        name = %s,
                        table_label = %s,
                        area = %s,
                        sub_zone = %s,
                        x_position = %s,
                        y_position = %s,
                        width = %s,
                        height = %s,
                        radius = %s,
                        shape = %s,
                        capacity = %s,
                        description = %s,
                        sort_order = %s,
                        is_active = 1
                    WHERE resource_code = %s
                    """,
                    floor_values,
                )

        existing_booking = existing_booking_rows.get(table["resource_code"])
        if not existing_booking:
            cursor.execute(
                """
                INSERT INTO booking_resources (
                    resource_code, area_name, resource_type, display_name, table_label,
                    seat_capacity, setup_key, image_url, description, sort_order, is_active
                )
                VALUES (%s,%s,'table',%s,%s,%s,NULL,NULL,%s,%s,1)
                """,
                (
                    table["resource_code"],
                    table["area"],
                    table["name"],
                    table["table_label"],
                    table["capacity"],
                    table["description"],
                    table["sort_order"],
                ),
            )
        elif (
            str(existing_booking.get("area_name") or "") != str(table["area"])
            or str(existing_booking.get("display_name") or "") != str(table["name"])
            or str(existing_booking.get("table_label") or "") != str(table["table_label"])
            or int(existing_booking.get("seat_capacity") or 0) != int(table["capacity"])
            or str(existing_booking.get("description") or "") != str(table["description"] or "")
            or int(existing_booking.get("sort_order") or 0) != int(table["sort_order"])
            or int(existing_booking.get("is_active") or 0) != 1
        ):
            cursor.execute(
                """
                UPDATE booking_resources
                SET
                    area_name = %s,
                    display_name = %s,
                    table_label = %s,
                    seat_capacity = %s,
                    description = %s,
                    sort_order = %s,
                    is_active = 1
                WHERE resource_code = %s
                """,
                (
                    table["area"],
                    table["name"],
                    table["table_label"],
                    table["capacity"],
                    table["description"],
                    table["sort_order"],
                    table["resource_code"],
                ),
            )

    cursor.execute(
        """
        UPDATE booking_resources
        SET is_active = 0
        WHERE resource_code IN ('main-11', 'main-12')
        """
    )


def get_floor_map_default_datetime(selected_date=None):
    today = date.today()
    if isinstance(selected_date, str) and selected_date:
        try:
            selected = datetime.strptime(selected_date, "%Y-%m-%d").date()
        except ValueError:
            selected = today
    elif isinstance(selected_date, date):
        selected = selected_date
    else:
        selected = today

    if selected > today:
        return datetime.combine(selected, time(hour=18, minute=0))

    base = datetime.now() + timedelta(minutes=30)
    rounded_minutes = 30 if base.minute > 0 and base.minute <= 30 else 0
    rounded_hour = base.hour + (1 if base.minute > 30 else 0)
    if rounded_hour >= 24:
        rounded_hour = 23
        rounded_minutes = 30
    return base.replace(hour=rounded_hour, minute=rounded_minutes, second=0, microsecond=0)


def get_floor_menu_catalog(cursor, selected_date):
    ensure_reservation_floor_schema(cursor)
    menu_catalog, nila_sizes, sea_fish = get_stock_context(cursor, selected_date)
    return enrich_menu_catalog_for_floor(menu_catalog), nila_sizes, sea_fish


def get_floor_tables(cursor):
    ensure_reservation_floor_schema(cursor)
    cursor.execute(
        """
        SELECT
            id,
            resource_code,
            name,
            table_label,
            area,
            sub_zone,
            x_position,
            y_position,
            width,
            height,
            radius,
            shape,
            capacity,
            COALESCE(description, '') AS description,
            is_active,
            sort_order
        FROM restaurant_tables
        WHERE area = %s
        ORDER BY sort_order, name
        """,
        (BOOKING_TABLE_AREA,),
    )
    return cursor.fetchall()


def enrich_menu_catalog_for_floor(menu_catalog):
    enriched = []
    for raw_menu in menu_catalog:
        if int(raw_menu.get("is_active", 1) or 0) == 0:
            continue

        menu = dict(raw_menu)
        feature_flags = MENU_FEATURE_MAP.get(_normalize_name(menu.get("name")))
        option_groups = [dict(group) for group in menu.get("option_groups", [])]
        seasoning_group = next((group for group in option_groups if group.get("key") == "seasoning"), None)
        generic_option_groups = [group for group in option_groups if group.get("key") != "seasoning"]
        menu["option_groups"] = option_groups
        menu["has_options"] = bool((feature_flags or {}).get("has_options") or menu.get("has_options") or option_groups)
        menu["has_seasoning"] = bool((feature_flags or {}).get("has_seasoning") or menu.get("has_seasoning") or seasoning_group)
        menu["seasoning_choices"] = (seasoning_group or {}).get("choices", []) or TAIWAN_SEASONING_CHOICES
        menu["generic_option_groups"] = generic_option_groups
        enriched.append(menu)

    return enriched


def _extract_table_codes_from_label(table_number):
    normalized = f" {str(table_number or '').lower()} "
    found_codes = []
    for label in TABLE_LABELS_BY_LENGTH:
        pattern = rf"(?<![a-z0-9]){re.escape(label)}(?![a-z0-9])"
        if re.search(pattern, normalized):
            found_codes.append(TABLE_CODE_BY_LABEL[label])
    return list(dict.fromkeys(found_codes))


def extract_reservation_table_codes(row):
    codes = []
    codes.extend(parse_resource_codes_value(row.get("booking_resource_codes")))
    if row.get("booking_resource_code"):
        codes.append(str(row.get("booking_resource_code")).strip())

    if not codes:
        codes.extend(_extract_table_codes_from_label(row.get("table_number")))

    expanded_codes = set()
    for code in codes:
        expanded_codes.update(_table_codes_for_resource(code))
    return expanded_codes


def get_reservation_end_datetime(row):
    reservation_datetime = row.get("reservation_datetime")
    booking_end_datetime = row.get("booking_end_datetime")
    duration_minutes = int(row.get("duration_minutes") or 0)

    if isinstance(reservation_datetime, str):
        reservation_datetime = datetime.strptime(reservation_datetime, "%Y-%m-%d %H:%M:%S")

    if isinstance(booking_end_datetime, str):
        booking_end_datetime = datetime.strptime(booking_end_datetime, "%Y-%m-%d %H:%M:%S")

    if booking_end_datetime:
        return booking_end_datetime

    if duration_minutes <= 0:
        duration_minutes = DEFAULT_RESERVATION_DURATION_MINUTES

    return reservation_datetime + timedelta(minutes=duration_minutes)


def get_overlapping_table_reservations(cursor, start_datetime, duration_minutes, exclude_reservation_id=None):
    ensure_reservation_floor_schema(cursor)
    end_datetime = start_datetime + timedelta(minutes=max(int(duration_minutes or 0), DEFAULT_RESERVATION_DURATION_MINUTES))
    # Overlap rule:
    # an existing reservation blocks the same table when its start time is before
    # the requested end time, and its computed end time is after the requested start time.
    # Cancelled/completed reservations are ignored so they do not block availability.
    query = """
        SELECT
            id,
            customer_name,
            table_number,
            reservation_datetime,
            booking_end_datetime,
            duration_minutes,
            status,
            booking_resource_code,
            booking_resource_codes
        FROM reservations
        WHERE reservation_datetime < %s
          AND COALESCE(
                booking_end_datetime,
                DATE_ADD(
                    reservation_datetime,
                    INTERVAL COALESCE(NULLIF(duration_minutes, 0), %s) MINUTE
                )
              ) > %s
    """
    params = [end_datetime, DEFAULT_RESERVATION_DURATION_MINUTES, start_datetime]

    if exclude_reservation_id:
        query += " AND id <> %s"
        params.append(exclude_reservation_id)

    cursor.execute(query, tuple(params))
    overlapping_rows = []
    for row in cursor.fetchall():
        current_status = str(row.get("status") or "confirmed").strip().lower()
        if current_status in NON_BLOCKING_RESERVATION_STATUSES or current_status not in RESERVATION_BLOCKING_STATUSES:
            continue
        row["blocking_codes"] = extract_reservation_table_codes(row)
        overlapping_rows.append(row)
    return overlapping_rows


def build_floor_availability(cursor, start_datetime, duration_minutes, exclude_reservation_id=None):
    tables = get_floor_tables(cursor)
    overlapping_rows = get_overlapping_table_reservations(
        cursor,
        start_datetime,
        duration_minutes,
        exclude_reservation_id=exclude_reservation_id,
    )

    availability_map = {}
    for table in tables:
        code = table["resource_code"]
        status_name = "available" if int(table.get("is_active") or 0) else "unavailable"
        status_label = "Available" if status_name == "available" else "Unavailable"
        severity = _status_severity(status_name)
        overlap_info = []

        for reservation in overlapping_rows:
            if code not in reservation.get("blocking_codes", set()):
                continue

            reservation_status = str(reservation.get("status") or "confirmed").strip().lower()
            candidate_status = "occupied" if reservation_status in ACTIVE_OCCUPANCY_STATUSES else "reserved"
            candidate_severity = _status_severity(candidate_status)
            overlap_info.append(
                {
                    "reservation_id": reservation["id"],
                    "customer_name": reservation.get("customer_name"),
                    "status": reservation_status or "confirmed",
                    "reservation_datetime": reservation.get("reservation_datetime"),
                    "booking_end_datetime": get_reservation_end_datetime(reservation),
                    "table_number": reservation.get("table_number"),
                }
            )
            if candidate_severity > severity:
                severity = candidate_severity
                status_name = candidate_status
                status_label = "Occupied" if candidate_status == "occupied" else "Reserved"

        availability_map[code] = {
            "status": status_name,
            "status_label": status_label,
            "is_selectable": status_name == "available",
            "conflicts": overlap_info,
        }

    return tables, availability_map, overlapping_rows


def get_floor_map_payload(cursor, start_datetime, duration_minutes, exclude_reservation_id=None):
    tables, availability_map, _ = build_floor_availability(
        cursor,
        start_datetime,
        duration_minutes,
        exclude_reservation_id=exclude_reservation_id,
    )
    payload_tables = []
    for table in tables:
        item = dict(table)
        item.update(availability_map.get(table["resource_code"], {}))
        payload_tables.append(item)
    return {"tables": payload_tables}


def get_table_detail_payload(cursor, resource_code, start_datetime, duration_minutes, exclude_reservation_id=None):
    tables, availability_map, _ = build_floor_availability(
        cursor,
        start_datetime,
        duration_minutes,
        exclude_reservation_id=exclude_reservation_id,
    )
    table = next((row for row in tables if row["resource_code"] == resource_code), None)
    if not table:
        return None
    payload = dict(table)
    payload.update(availability_map.get(resource_code, {}))
    return payload


def build_floor_table_label(table_row):
    return serialize_resource_selection(
        [
            {
                "area_name": BOOKING_TABLE_AREA,
                "table_label": table_row.get("table_label"),
                "display_name": table_row.get("name"),
            }
        ]
    )


def _build_option_entry(label, choice):
    return {
        "label": label,
        "value": choice["value"],
        "display": choice["label"],
    }


def build_menu_options_payload_from_client(menu_catalog, item):
    display_menu_id = str(item.get("display_menu_id") or "").strip()
    selected_menu = next((menu for menu in menu_catalog if str(menu.get("id")) == display_menu_id), None)
    if not selected_menu:
        return item.get("menu_options_json") or None

    selected_options = {}

    for group in selected_menu.get("generic_option_groups", []):
        option_key = group.get("key")
        raw_value = item.get("option_values", {}).get(option_key)
        choices = group.get("choices", [])
        if group.get("multiple"):
            selected_values = raw_value if isinstance(raw_value, list) else [raw_value] if raw_value else []
            choice_map = {str(choice.get("value")): choice for choice in choices}
            chosen_entries = [choice_map.get(str(value)) for value in selected_values if choice_map.get(str(value))]
            if chosen_entries:
                selected_options[option_key] = {
                    "label": group.get("label"),
                    "value": [entry["value"] for entry in chosen_entries],
                    "display": [entry["label"] for entry in chosen_entries],
                }
        else:
            choice = next((choice for choice in choices if str(choice.get("value")) == str(raw_value)), None)
            if not choice and choices:
                choice = choices[0]
            if choice:
                selected_options[option_key] = _build_option_entry(group.get("label"), choice)

    seasoning_value = str(item.get("seasoning") or "").strip()
    seasoning_group = next((group for group in selected_menu.get("option_groups", []) if group.get("key") == "seasoning"), None)
    if seasoning_group and seasoning_value:
        seasoning_choice = next(
            (choice for choice in seasoning_group.get("choices", []) if str(choice.get("value")) == seasoning_value),
            None,
        )
        if seasoning_choice:
            selected_options["seasoning"] = _build_option_entry(seasoning_group.get("label"), seasoning_choice)

    if not selected_options:
        return item.get("menu_options_json") or None

    return json.dumps(
        {
            "display_menu_id": selected_menu.get("id"),
            "display_name": selected_menu.get("name"),
            "selected_options": selected_options,
        },
        ensure_ascii=False,
    )


def parse_floor_order_items(raw_payload):
    if not raw_payload:
        raise ValueError("Pilih minimal 1 menu sebelum menyimpan reservasi.")

    try:
        items = json.loads(raw_payload)
    except (TypeError, ValueError, json.JSONDecodeError):
        raise ValueError("Data menu reservasi tidak valid.")

    if not isinstance(items, list):
        raise ValueError("Format daftar menu reservasi tidak dikenali.")

    normalized_items = []
    for item in items:
        if not isinstance(item, dict):
            continue
        try:
            qty_value = int(item.get("qty") or 0)
        except (TypeError, ValueError):
            raise ValueError("Jumlah menu tidak valid.")
        normalized_items.append(
            {
                "display_menu_id": str(item.get("display_menu_id") or "").strip(),
                "menu_id": str(item.get("menu_id") or "").strip(),
                "qty": qty_value,
                "seasoning": str(item.get("seasoning") or "").strip(),
                "option_values": item.get("option_values") if isinstance(item.get("option_values"), dict) else {},
                "menu_options_json": item.get("menu_options_json") or None,
                "fish_type": (item.get("fish_type") or "").strip() or None,
                "fish_size": (item.get("fish_size") or "").strip() or None,
                "fish_weight": item.get("fish_weight") or None,
                "fish_stock_id": item.get("fish_stock_id") or None,
                "special_stock_id": item.get("special_stock_id") or None,
                "special_request_text": (item.get("special_request_text") or "").strip() or None,
            }
        )

    normalized_items = [item for item in normalized_items if item.get("display_menu_id")]
    if not normalized_items:
        raise ValueError("Pilih minimal 1 menu sebelum menyimpan reservasi.")
    return normalized_items


def _normalize_customer_status(value):
    raw_status = str(value or "confirmed").strip().lower()
    return raw_status if raw_status in {"pending", "confirmed", "occupied", "completed", "cancelled"} else "confirmed"


def create_floor_reservation(
    conn,
    cursor,
    reservation_payload,
    menu_catalog,
    selected_table,
    actor=None,
):
    customer_name = str(reservation_payload.get("customer_name") or "").strip()
    whatsapp_number = str(reservation_payload.get("whatsapp_number") or "").strip() or None
    reservation_datetime = reservation_payload.get("reservation_datetime")
    duration_minutes = int(reservation_payload.get("duration_minutes") or DEFAULT_RESERVATION_DURATION_MINUTES)
    people_count = int(reservation_payload.get("people_count") or 0)
    description = str(reservation_payload.get("description") or "").strip() or None
    reservation_status = _normalize_customer_status(reservation_payload.get("status"))
    order_items = reservation_payload.get("items") or []

    if not customer_name:
        raise ValueError("Nama customer wajib diisi.")
    if people_count <= 0:
        raise ValueError("Jumlah tamu harus lebih dari 0.")
    if duration_minutes <= 0:
        raise ValueError("Durasi reservasi harus lebih dari 0 menit.")
    if not isinstance(reservation_datetime, datetime):
        raise ValueError("Tanggal reservasi tidak valid.")
    if not selected_table:
        raise ValueError("Pilih meja dari denah terlebih dahulu.")
    if int(selected_table.get("capacity") or 0) > 0 and people_count > int(selected_table.get("capacity") or 0):
        raise ValueError("Jumlah tamu melebihi kapasitas meja yang dipilih.")
    if not order_items:
        raise ValueError("Pilih minimal 1 menu sebelum menyimpan reservasi.")

    availability = get_table_detail_payload(cursor, selected_table["resource_code"], reservation_datetime, duration_minutes)
    if not availability or availability.get("status") != "available":
        raise ValueError("Meja yang dipilih sudah tidak tersedia pada jam tersebut.")

    reservation_end_datetime = reservation_datetime + timedelta(minutes=duration_minutes)
    reservation_date = reservation_datetime.strftime("%Y-%m-%d")
    resource_code = selected_table["resource_code"]
    serialized_table_label = build_floor_table_label(selected_table)

    cursor.execute(
        """
        INSERT INTO reservations (
            customer_name,
            whatsapp_number,
            table_number,
            people_count,
            reservation_datetime,
            duration_minutes,
            status,
            booking_end_datetime,
            booking_source,
            booking_area,
            booking_resource_code,
            booking_resource_codes,
            description
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'panel_floor_map',%s,%s,%s,%s)
        """,
        (
            customer_name,
            whatsapp_number,
            serialized_table_label,
            people_count,
            reservation_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            duration_minutes,
            reservation_status,
            reservation_end_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            BOOKING_TABLE_AREA,
            resource_code,
            json.dumps([resource_code], ensure_ascii=False),
            description,
        ),
    )
    reservation_id = cursor.lastrowid
    log_reservation_history(
        cursor,
        reservation_id,
        "create",
        "reservation",
        f"Reservasi dibuat untuk {customer_name}, meja {selected_table.get('table_label')}, pax {people_count}.",
        actor=actor or "system",
    )

    for item in order_items:
        if int(item.get("qty") or 0) <= 0:
            raise ValueError("Jumlah menu harus minimal 1.")

        selected_menu = next((menu for menu in menu_catalog if str(menu.get("id")) == str(item.get("display_menu_id"))), None)
        if not selected_menu:
            raise ValueError("Ada menu yang tidak ditemukan. Silakan pilih ulang.")

        if selected_menu.get("has_seasoning") and not str(item.get("seasoning") or "").strip():
            raise ValueError(f"Bumbu wajib dipilih untuk {selected_menu.get('name')}.")

        menu_options_json = build_menu_options_payload_from_client(menu_catalog, item)
        resolved_menu_id = resolve_menu_submission(
            menu_catalog,
            item.get("menu_id"),
            display_menu_id=item.get("display_menu_id"),
            menu_options_json=menu_options_json,
        )
        if resolved_menu_id is None:
            raise ValueError(f"Pilihan menu untuk {selected_menu.get('name')} belum lengkap.")

        fish_type = item.get("fish_type")
        fish_size = item.get("fish_size")
        fish_weight = item.get("fish_weight")
        if fish_weight in ("", "0", "0.0"):
            fish_weight = None

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
            menu_options_json=menu_options_json,
        )
        if not is_valid_stock:
            raise ValueError(stock_message)

        special_request_text = str(item.get("special_request_text") or "").strip() or None
        special_request_value = "with_special" if special_request_text else "no_special"

        cursor.execute(
            """
            INSERT INTO reservation_items (
                reservation_id,
                menu_id,
                quantity,
                special_request,
                dish_description,
                fish_type,
                fish_size,
                fish_weight,
                fish_stock_ref_id,
                special_stock_ref_id,
                menu_options_json
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                reservation_id,
                resolved_menu_id,
                int(item.get("qty") or 0),
                special_request_value,
                special_request_text,
                fish_type,
                fish_size,
                fish_weight,
                resolved_fish_stock_id,
                resolved_special_stock_id,
                menu_options_json or None,
            ),
        )
        reservation_item_id = cursor.lastrowid

        log_reservation_history(
            cursor,
            reservation_id,
            "create",
            "menu",
            build_menu_history_summary(
                "create",
                get_menu_label_for_history(cursor, resolved_menu_id, menu_options_json=menu_options_json),
                qty=item.get("qty"),
                note=build_menu_display_note(menu_options_json, special_request_text),
            ),
            actor=actor or "system",
            reservation_item_id=reservation_item_id,
        )

        reduce_stock_after_order(
            cursor,
            fish_stock_id=resolved_fish_stock_id,
            special_stock_id=resolved_special_stock_id,
            qty=int(item.get("qty") or 0),
        )

    conn.commit()
    return reservation_id
