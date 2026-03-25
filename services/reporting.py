from collections import OrderedDict

from services.common import (
    dish_description_sql,
    format_fish_info,
    format_menu_label,
    format_weight_display,
    normalize_text,
)
from services.menu_options import (
    build_option_summary_from_payload,
    format_option_display_value,
    get_effective_selected_options,
    get_payload_display_name,
    normalize_option_value_list,
    normalize_serving_type,
)


FRIED_RICE_MENU_NAMES = (
    "nasi goreng kampung",
    "nasi goreng spesial",
    "nasi goreng sagela",
)

DASHBOARD_TABLE_CONFIGS = OrderedDict(
    [
        (
            "fish_stock",
            {
                "label": "Total Ikan",
                "title": "Total Ikan Hari Ini",
                "description": "Tabel ini terpisah dari filter divisi dan dihitung berdasarkan tanggal yang dipilih.",
                "empty_message": "Belum ada total ikan pada tanggal ini.",
                "table_class": "w-full text-left",
                "excel_title": "TOTAL STOCK IKAN YANG DIBUTUHKAN HARI INI",
                "excel_table_name": "RekapIkan",
                "excel_style_name": "TableStyleMedium4",
                "compact_number_keys": {"no", "total"},
                "columns": [
                    {"key": "no", "label": "No"},
                    {"key": "fish_divisi", "label": "Divisi"},
                    {"key": "fish_name", "label": "Jenis Ikan"},
                    {"key": "fish_size", "label": "Ukuran"},
                    {"key": "fish_weight_display", "label": "Berat"},
                    {"key": "total", "label": "Jumlah"},
                    {"key": "menu_names", "label": "Menu"},
                ],
            },
        ),
        (
            "rice_need",
            {
                "label": "Kebutuhan Nasi",
                "title": "Rekap Kebutuhan Nasi Hari Ini",
                "description": "",
                "empty_message": "Belum ada kebutuhan nasi pada tanggal ini.",
                "table_class": "w-full text-left",
                "excel_title": "REKAP KEBUTUHAN NASI HARI INI",
                "excel_table_name": "RekapNasi",
                "excel_style_name": "TableStyleMedium2",
                "compact_number_keys": {"no", "jumlah"},
                "columns": [
                    {"key": "no", "label": "No"},
                    {"key": "keterangan", "label": "Keterangan"},
                    {"key": "jumlah", "label": "Jumlah"},
                ],
            },
        ),
        (
            "fried_rice",
            {
                "label": "Total Nasi Goreng",
                "title": "Total Sambal Nasi Goreng",
                "description": "",
                "empty_message": "Belum ada total nasi goreng pada tanggal ini.",
                "table_class": "w-full text-left",
                "excel_title": "TOTAL SAMBAL NASI GORENG",
                "excel_table_name": "RekapNasiGoreng",
                "excel_style_name": "TableStyleMedium3",
                "compact_number_keys": {"no", "jumlah"},
                "columns": [
                    {"key": "no", "label": "No"},
                    {"key": "menu", "label": "Menu"},
                    {"key": "jumlah", "label": "Jumlah"},
                ],
            },
        ),
        (
            "menu_total",
            {
                "label": "Total Jumlah Makanan Permenu",
                "title": "TOTAL MENU UNTUK KITCHEN",
                "description": "Menu digabung per nama dasar. PCS dan paket dijumlahkan menjadi satu total, dengan ringkasan detail order, penyajian saus sate, dan special request.",
                "empty_message": "Belum ada total menu kitchen pada tanggal ini.",
                "table_class": "w-full text-left",
                "excel_title": "TOTAL MENU UNTUK KITCHEN",
                "excel_table_name": "RekapMenuGabungan",
                "excel_style_name": "TableStyleMedium6",
                "compact_number_keys": {"no", "jumlah"},
                "columns": [
                    {"key": "no", "label": "No"},
                    {"key": "divisi", "label": "Divisi"},
                    {"key": "menu", "label": "Nama Menu"},
                    {"key": "jumlah", "label": "Jumlah"},
                    {"key": "special_req", "label": "Special Req"},
                    {"key": "penyajian_saus", "label": "Keterangan Saus"},
                    {"key": "detail", "label": "Keterangan"},
                ],
            },
        ),
        (
            "menu_total_detail",
            {
                "label": "Total Menu Detail",
                "title": "TOTAL MENU UNTUK PLATING",
                "description": "Menu dipisah per tipe serving seperti PCS, Paket, atau Porsi, lengkap dengan detail order, penyajian saus sate, dan special request.",
                "empty_message": "Belum ada detail menu pada tanggal ini.",
                "table_class": "w-full text-left",
                "excel_title": "TOTAL MENU UNTUK PLATING",
                "excel_table_name": "RekapMenuDetail",
                "excel_style_name": "TableStyleMedium7",
                "compact_number_keys": {"no", "jumlah"},
                "columns": [
                    {"key": "no", "label": "No"},
                    {"key": "divisi", "label": "Divisi"},
                    {"key": "menu", "label": "Menu"},
                    {"key": "jumlah", "label": "Jumlah"},
                    {"key": "special_req", "label": "Special Req"},
                    {"key": "penyajian_saus", "label": "Penyajian Saus"},
                    {"key": "detail", "label": "Keterangan"},
                ],
            },
        ),
    ]
)

EXPORT_TABLE_KEYS = set(DASHBOARD_TABLE_CONFIGS.keys())


def parse_table_filters(requested_tables, use_table_filters=False):
    normalized_tables = {normalize_text(table_key) for table_key in requested_tables if (table_key or "").strip()}

    if not normalized_tables:
        if use_table_filters:
            return {"menu_total"}
        return set(EXPORT_TABLE_KEYS)

    selected_tables = normalized_tables & EXPORT_TABLE_KEYS
    return selected_tables or set(EXPORT_TABLE_KEYS)


def get_default_dashboard_column_keys(table_key):
    return [column["key"] for column in DASHBOARD_TABLE_CONFIGS.get(table_key, {}).get("columns", [])]


def parse_dashboard_column_filters(request_args, selected_tables):
    selected_columns = {}

    for table_key in DASHBOARD_TABLE_CONFIGS:
        if table_key not in selected_tables:
            continue

        available_columns = DASHBOARD_TABLE_CONFIGS.get(table_key, {}).get("columns", [])
        available_column_keys = {normalize_text(column.get("key")) for column in available_columns}
        requested_keys = [
            normalize_text(column_key)
            for column_key in request_args.getlist(f"columns_{table_key}")
            if (column_key or "").strip()
        ]

        if not requested_keys:
            selected_columns[table_key] = get_default_dashboard_column_keys(table_key)
            continue

        filtered_keys = [
            column["key"]
            for column in available_columns
            if normalize_text(column.get("key")) in available_column_keys
            and normalize_text(column.get("key")) in requested_keys
        ]
        selected_columns[table_key] = filtered_keys or get_default_dashboard_column_keys(table_key)

    return selected_columns


def get_selected_dashboard_column_defs(selected_tables, selected_columns):
    selected_column_defs = OrderedDict()

    for table_key, config in DASHBOARD_TABLE_CONFIGS.items():
        if table_key not in selected_tables:
            continue

        allowed_keys = set(selected_columns.get(table_key) or get_default_dashboard_column_keys(table_key))
        selected_column_defs[table_key] = [column for column in config.get("columns", []) if column.get("key") in allowed_keys]

    return selected_column_defs


def map_sequence_rows(rows, column_keys):
    mapped_rows = []
    for row in rows:
        mapped_rows.append({column_key: row[index] if index < len(row) else "-" for index, column_key in enumerate(column_keys)})
    return mapped_rows


def build_dashboard_table_rows(fish_totals, rice_requirement_rows, fried_rice_rows, combined_menu_rows, detailed_menu_rows):
    return {
        "fish_stock": [
            {
                "no": row["no"],
                "fish_divisi": row["fish_divisi"],
                "fish_name": row["fish_name"],
                "fish_size": row["fish_size"] or "-",
                "fish_weight_display": row["fish_weight_display"] if row["fish_weight"] and row["fish_weight"] > 0 else "-",
                "total": row["total"],
                "menu_names": row["menu_names"] or "-",
            }
            for row in fish_totals
        ],
        "rice_need": map_sequence_rows(rice_requirement_rows, ["no", "keterangan", "jumlah"]),
        "fried_rice": map_sequence_rows(fried_rice_rows, ["no", "menu", "jumlah"]),
        "menu_total": [
            {
                "no": row["no"],
                "divisi": row["divisi"],
                "menu": row["menu"],
                "detail": row["detail"],
                "penyajian_saus": row["penyajian_saus"],
                "special_req": row["special_req"],
                "jumlah": row["jumlah"],
            }
            for row in combined_menu_rows
        ],
        "menu_total_detail": [
            {
                "no": row["no"],
                "divisi": row["divisi"],
                "menu": row["menu"],
                "detail": row["detail"],
                "penyajian_saus": row["penyajian_saus"],
                "special_req": row["special_req"],
                "jumlah": row["jumlah"],
            }
            for row in detailed_menu_rows
        ],
    }


def get_daily_menu_recap_rows(cursor, selected_date, selected_divisi=None, search_query=""):
    description_expr = dish_description_sql("ri")
    query = """
    SELECT
        m.name,
        m.serving_type,
        CASE
            WHEN LOWER(m.name) = 'udang sambal pete' THEN 'lokal'
            WHEN m.divisi IN ('local','bakar/local') THEN 'lokal'
            WHEN m.divisi IN ('seafood','bakar/seafood') THEN 'seafood'
            ELSE m.divisi
        END AS divisi,
        COALESCE(NULLIF(TRIM(ri.fish_type),''),'') AS fish_type,
        ri.fish_size,
        COALESCE(ri.fish_weight,0) AS fish_weight,
        COALESCE(fs.weight_unit, ds.weight_unit, 'ons') AS fish_weight_unit,
    """ + description_expr + """ AS dish_description,
        ri.menu_options_json,
        SUM(ri.quantity) AS total
    FROM reservation_items ri
    JOIN menus m ON m.id = ri.menu_id
    LEFT JOIN fish_stock fs ON fs.id = ri.fish_stock_ref_id
    LEFT JOIN daily_item_stock ds ON ds.id = ri.special_stock_ref_id
    JOIN reservations r ON r.id = ri.reservation_id
    WHERE DATE(r.reservation_datetime) = %s
    """

    params = [selected_date]
    if selected_divisi:
        if selected_divisi == "lokal":
            query += " AND m.divisi IN (%s,%s)"
            params.extend(["local", "bakar/local"])
        elif selected_divisi == "seafood":
            query += " AND m.divisi IN (%s,%s)"
            params.extend(["seafood", "bakar/seafood"])
        else:
            query += " AND m.divisi = %s"
            params.append(selected_divisi)

    search_query = (search_query or "").strip()
    if search_query:
        query += " AND m.name LIKE %s"
        params.append(f"%{search_query}%")

    query += """
    GROUP BY
        m.name,
        m.serving_type,
        CASE
            WHEN LOWER(m.name) = 'udang sambal pete' THEN 'lokal'
            WHEN m.divisi IN ('local','bakar/local') THEN 'lokal'
            WHEN m.divisi IN ('seafood','bakar/seafood') THEN 'seafood'
            ELSE m.divisi
        END,
        COALESCE(NULLIF(TRIM(ri.fish_type),''),''),
        ri.fish_size,
        COALESCE(ri.fish_weight,0),
        COALESCE(fs.weight_unit, ds.weight_unit, 'ons'),
        ri.menu_options_json,
    """ + description_expr + """
    ORDER BY divisi, m.name, m.serving_type, total DESC
    """

    cursor.execute(query, params)
    rows = cursor.fetchall()

    for index, row in enumerate(rows, start=1):
        row["no"] = index
        row["menu_label"] = get_payload_display_name(row.get("menu_options_json"), row.get("name"), row.get("serving_type"))
        row["fish_info"] = format_fish_info(row)
        row["effective_selected_options"] = get_effective_selected_options(row)
        row["option_summary"] = " | ".join(
            f"{(option.get('label') or '').strip()}: {format_option_display_value(option.get('display'))}"
            for option in row["effective_selected_options"].values()
            if (option.get("label") or "").strip() and format_option_display_value(option.get("display"))
        )
        row["display_note"] = " | ".join(part for part in [row["option_summary"], (row.get("dish_description") or "").strip()] if part)

    return rows


def get_daily_menu_serving_totals(cursor, selected_date, selected_divisi=None):
    query = """
    SELECT
        m.name,
        m.serving_type,
        SUM(ri.quantity) AS total
    FROM reservation_items ri
    JOIN menus m ON m.id = ri.menu_id
    JOIN reservations r ON r.id = ri.reservation_id
    WHERE DATE(r.reservation_datetime) = %s
    """
    params = [selected_date]

    if selected_divisi:
        if selected_divisi == "lokal":
            query += " AND m.divisi IN (%s,%s)"
            params.extend(["local", "bakar/local"])
        elif selected_divisi == "seafood":
            query += " AND m.divisi IN (%s,%s)"
            params.extend(["seafood", "bakar/seafood"])
        else:
            query += " AND m.divisi = %s"
            params.append(selected_divisi)

    query += """
    GROUP BY m.name, m.serving_type
    ORDER BY m.name, m.serving_type
    """

    cursor.execute(query, params)
    return cursor.fetchall()


def ensure_kitchen_live_tables(cursor):
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS reservation_item_completion (
        id INT AUTO_INCREMENT PRIMARY KEY,
        reservation_item_id INT NOT NULL,
        is_completed TINYINT(1) NOT NULL DEFAULT 0,
        completed_at DATETIME NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        UNIQUE KEY uniq_reservation_item_completion (reservation_item_id),
        CONSTRAINT fk_reservation_item_completion_item
            FOREIGN KEY (reservation_item_id) REFERENCES reservation_items(id)
            ON DELETE CASCADE
    )
    """
    )


def get_kitchen_live_reservations(cursor, selected_date, search_query=""):
    ensure_kitchen_live_tables(cursor)
    description_expr = dish_description_sql("ri")
    query = """
    SELECT
        r.id AS reservation_id,
        r.customer_name,
        r.table_number,
        r.people_count,
        r.reservation_datetime,
        r.description AS reservation_description,
        ri.id AS item_id,
        ri.quantity,
        COALESCE(NULLIF(TRIM(ri.fish_type),''),'') AS fish_type,
        ri.fish_size,
        COALESCE(ri.fish_weight,0) AS fish_weight,
        COALESCE(fs.weight_unit, ds.weight_unit, 'ons') AS fish_weight_unit,
    """ + description_expr + """ AS dish_description,
        ri.menu_options_json,
        m.name AS menu_name,
        m.serving_type,
        CASE
            WHEN LOWER(m.name) = 'udang sambal pete' THEN 'lokal'
            WHEN m.divisi IN ('local','bakar/local') THEN 'lokal'
            WHEN m.divisi IN ('seafood','bakar/seafood') THEN 'seafood'
            ELSE m.divisi
        END AS divisi,
        COALESCE(ric.is_completed, 0) AS is_completed
    FROM reservations r
    LEFT JOIN reservation_items ri ON ri.reservation_id = r.id
    LEFT JOIN menus m ON m.id = ri.menu_id
    LEFT JOIN fish_stock fs ON fs.id = ri.fish_stock_ref_id
    LEFT JOIN daily_item_stock ds ON ds.id = ri.special_stock_ref_id
    LEFT JOIN reservation_item_completion ric ON ric.reservation_item_id = ri.id
    WHERE DATE(r.reservation_datetime) = %s
    """
    params = [selected_date]

    if search_query:
        search_like = f"%{search_query}%"
        query += """
        AND (
            r.customer_name LIKE %s
            OR r.table_number LIKE %s
            OR COALESCE(r.description,'') LIKE %s
            OR CAST(r.id AS CHAR) LIKE %s
        )
        """
        params.extend([search_like] * 4)

    query += """
    ORDER BY r.reservation_datetime ASC, r.id ASC, ri.id ASC
    """
    cursor.execute(query, params)

    grouped_reservations = OrderedDict()
    for row in cursor.fetchall():
        reservation_id = row["reservation_id"]
        reservation = grouped_reservations.setdefault(
            reservation_id,
            {
                "reservation_id": reservation_id,
                "customer_name": row["customer_name"],
                "table_number": row["table_number"],
                "people_count": row["people_count"],
                "reservation_datetime": row["reservation_datetime"],
                "reservation_description": row.get("reservation_description"),
                "menus": [],
                "total_items": 0,
                "completed_items": 0,
                "all_completed": False,
            },
        )

        if row.get("item_id"):
            menu_item = {
                "item_id": row["item_id"],
                "menu_name": row.get("menu_name") or "-",
                "serving_type": row.get("serving_type") or "-",
                "divisi": row.get("divisi") or "-",
                "quantity": row.get("quantity") or 0,
                "dish_description": row.get("dish_description"),
                "menu_display_name": get_payload_display_name(row.get("menu_options_json"), row.get("menu_name"), row.get("serving_type")),
                "option_summary": build_option_summary_from_payload(row.get("menu_options_json")),
                "is_completed": bool(row.get("is_completed")),
            }
            menu_item["fish_info"] = format_fish_info(row)
            reservation["menus"].append(menu_item)

    for reservation in grouped_reservations.values():
        reservation["total_items"] = len(reservation["menus"])
        reservation["completed_items"] = sum(1 for item in reservation["menus"] if item["is_completed"])
        reservation["all_completed"] = reservation["total_items"] > 0 and reservation["completed_items"] == reservation["total_items"]

    return list(grouped_reservations.values())


def to_int_qty(value):
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def build_rice_requirement_rows(menu_totals):
    total_paket = sum(to_int_qty(row.get("total")) for row in menu_totals if normalize_serving_type(row.get("serving_type")) == "paket")
    nasi_putih_total = sum(to_int_qty(row.get("total")) for row in menu_totals if normalize_text(row.get("name")) == "nasi putih")
    total_nasi = total_paket + nasi_putih_total

    return [
        [1, "Total Nasi dari Menu Paket", total_paket],
        [2, "Total Nasi Putih Perpcs", nasi_putih_total],
        [3, "TOTAL KEBUTUHAN NASI", total_nasi],
    ]


def build_fried_rice_rows(menu_totals):
    totals_by_name = {}
    for row in menu_totals:
        name_key = normalize_text(row.get("name"))
        totals_by_name[name_key] = totals_by_name.get(name_key, 0) + to_int_qty(row.get("total"))

    rows = []
    for index, menu_name in enumerate(FRIED_RICE_MENU_NAMES, start=1):
        rows.append([index, menu_name.title(), totals_by_name.get(menu_name, 0)])

    total_fried_rice = sum(item[2] for item in rows)
    rows.append([len(rows) + 1, "Jumlah Sambal Nasgor", total_fried_rice])
    return rows


def increment_counter(counter, value, amount):
    normalized_value = str(value or "").strip()
    if not normalized_value:
        return
    counter[normalized_value] = counter.get(normalized_value, 0) + to_int_qty(amount)


def increment_labeled_counter(counter_map, label, values, amount):
    clean_label = str(label or "").strip()
    if not clean_label:
        return

    bucket = counter_map.setdefault(clean_label, OrderedDict())
    for value in normalize_option_value_list(values):
        increment_counter(bucket, value, amount)


def format_counter_text(counter):
    return format_counter_text_with_style(counter)


def format_counter_text_with_style(counter, use_parentheses=False):
    if not counter:
        return "-"

    ordered_values = sorted(counter.items(), key=lambda item: (-item[1], normalize_text(item[0])))
    if use_parentheses:
        return ", ".join(f"{value} ({count})" for value, count in ordered_values)
    return ", ".join(f"{value} {count}" for value, count in ordered_values)


def build_option_breakdown_text(option_counter_map):
    return build_option_breakdown_text_with_style(option_counter_map)


def build_option_breakdown_text_with_style(option_counter_map, use_parentheses=False):
    sections = []
    for label, values in option_counter_map.items():
        if not values:
            continue
        value_text = format_counter_text_with_style(values, use_parentheses=use_parentheses)
        sections.append(f"{label}: {value_text}")
    return " | ".join(sections)


def build_menu_dashboard_bucket(menu_name, divisi_name):
    return {
        "menu_name": menu_name,
        "divisi_set": {divisi_name},
        "sambal": OrderedDict(),
        "bumbu": OrderedDict(),
        "topping_saus": OrderedDict(),
        "suhu_minuman": OrderedDict(),
        "pilihan_telur": OrderedDict(),
        "pilihan_saus": OrderedDict(),
        "varian_ukuran": OrderedDict(),
        "opsi_lain": OrderedDict(),
        "size_nila": OrderedDict(),
        "berat_ikan": OrderedDict(),
        "sauce_presentation": OrderedDict(),
        "special_requests": OrderedDict(),
        "total": 0,
    }


def apply_row_to_dashboard_bucket(bucket, row):
    qty = to_int_qty(row.get("total"))
    selected_options = row.get("effective_selected_options") or get_effective_selected_options(row)

    for option in selected_options.values():
        label = (option.get("label") or "").strip()
        display_values = normalize_option_value_list(option.get("display"))
        if not label or not display_values:
            continue

        normalized_label = normalize_text(label)
        if normalized_label == normalize_text("Pilih Paket atau PCS"):
            continue
        if normalized_label == normalize_text("Sambal Rica"):
            for display_value in display_values:
                increment_counter(bucket["sambal"], display_value, qty)
            continue
        if normalized_label == normalize_text("Bumbu"):
            for display_value in display_values:
                increment_counter(bucket["bumbu"], display_value, qty)
            continue
        if normalized_label == normalize_text("Topping Saus"):
            for display_value in display_values:
                increment_counter(bucket["topping_saus"], display_value, qty)
            continue
        if normalized_label == normalize_text("Suhu Minuman"):
            for display_value in display_values:
                increment_counter(bucket["suhu_minuman"], display_value, qty)
            continue
        if normalized_label == normalize_text("Pilihan Telur"):
            for display_value in display_values:
                increment_counter(bucket["pilihan_telur"], display_value, qty)
            continue
        if normalized_label == normalize_text("Penyajian Saus"):
            for display_value in display_values:
                increment_counter(bucket["sauce_presentation"], display_value, qty)
            continue
        if normalized_label in (normalize_text("Pilihan Saus"), normalize_text("Penyajian Saus")):
            increment_labeled_counter(bucket["pilihan_saus"], label, display_values, qty)
            continue
        if normalized_label in (normalize_text("Varian Ayam"), normalize_text("Ukuran")):
            increment_labeled_counter(bucket["varian_ukuran"], label, display_values, qty)
            continue

        increment_labeled_counter(bucket["opsi_lain"], label, display_values, qty)

    fish_size = str(row.get("fish_size") or "").strip()
    if fish_size:
        increment_counter(bucket["size_nila"], fish_size.replace("_", " ").title(), qty)

    fish_weight = row.get("fish_weight")
    if fish_weight not in (None, "", 0, 0.0, "0", "0.0"):
        increment_counter(bucket["berat_ikan"], format_weight_display(fish_weight, row.get("fish_weight_unit")), qty)

    note = (row.get("dish_description") or "").strip()
    if note and note != "-":
        increment_counter(bucket["special_requests"], note, qty)

    bucket["total"] += qty


def build_dashboard_detail_text(bucket):
    sections = []

    section_map = [
        ("Sambal", bucket["sambal"]),
        ("Bumbu", bucket["bumbu"]),
        ("Topping / Saus", bucket["topping_saus"]),
        ("Suhu", bucket["suhu_minuman"]),
        ("Telur", bucket["pilihan_telur"]),
        ("Size Nila", bucket["size_nila"]),
        ("Berat Ikan", bucket["berat_ikan"]),
    ]
    for label, counter in section_map:
        text = format_counter_text_with_style(counter, use_parentheses=True)
        if text != "-":
            sections.append(f"{label}: {text}")

    for option_text in [
        build_option_breakdown_text_with_style(bucket["pilihan_saus"], use_parentheses=True),
        build_option_breakdown_text_with_style(bucket["varian_ukuran"], use_parentheses=True),
        build_option_breakdown_text_with_style(bucket["opsi_lain"], use_parentheses=True),
    ]:
        if option_text:
            sections.append(option_text)

    return " | ".join(sections) or "-"


def build_dashboard_row_output(index, bucket):
    return {
        "no": index,
        "divisi": ", ".join(sorted(bucket["divisi_set"], key=normalize_text)),
        "menu": bucket["menu_name"],
        "detail": build_dashboard_detail_text(bucket),
        "penyajian_saus": format_counter_text_with_style(bucket["sauce_presentation"], use_parentheses=True),
        "special_req": format_counter_text_with_style(bucket["special_requests"], use_parentheses=True),
        "jumlah": bucket["total"],
    }


def build_combined_menu_rows(menu_rows):
    combined_totals = {}

    for row in menu_rows:
        base_name = get_payload_display_name(row.get("menu_options_json"), row.get("name"), row.get("serving_type"))
        base_key = normalize_text(base_name)
        divisi_name = (row.get("divisi") or "-").strip() or "-"

        if base_key not in combined_totals:
            combined_totals[base_key] = build_menu_dashboard_bucket(base_name, divisi_name)

        combined_totals[base_key]["divisi_set"].add(divisi_name)
        apply_row_to_dashboard_bucket(combined_totals[base_key], row)

    ordered_rows = sorted(combined_totals.values(), key=lambda item: (-item["total"], normalize_text(item["menu_name"])))
    return [build_dashboard_row_output(index, row) for index, row in enumerate(ordered_rows, start=1)]


def build_detailed_menu_rows(menu_rows):
    grouped_rows = OrderedDict()

    sorted_rows = sorted(
        menu_rows,
        key=lambda row: (
            normalize_text(row.get("divisi")),
            normalize_text(get_payload_display_name(row.get("menu_options_json"), row.get("name"), row.get("serving_type"))),
            normalize_serving_type(row.get("serving_type")),
        ),
    )

    for row in sorted_rows:
        base_menu_name = get_payload_display_name(row.get("menu_options_json"), row.get("name"), row.get("serving_type"))
        menu_name = format_menu_label(base_menu_name, row.get("serving_type"))
        row_key = normalize_text(menu_name)
        bucket = grouped_rows.setdefault(row_key, build_menu_dashboard_bucket(menu_name, row.get("divisi") or "-"))
        bucket["divisi_set"].add((row.get("divisi") or "-").strip() or "-")
        apply_row_to_dashboard_bucket(bucket, row)

    return [build_dashboard_row_output(index, row) for index, row in enumerate(grouped_rows.values(), start=1)]


def get_daily_fish_totals(cursor, selected_date):
    cursor.execute(
        """
    SELECT
        CASE
            WHEN m.divisi IN ('local','bakar/local') THEN 'local'
            WHEN m.divisi IN ('seafood','bakar/seafood') THEN 'seafood'
            ELSE m.divisi
        END AS fish_divisi,
        CASE
            WHEN LOWER(TRIM(COALESCE(ri.fish_type,''))) = 'rahang tuna' THEN 'Rahang Tuna PCS'
            WHEN COALESCE(NULLIF(TRIM(ri.fish_size),''),'') <> '' THEN 'Nila'
            WHEN COALESCE(NULLIF(TRIM(ri.fish_type),''),'') <> '' THEN CONCAT(UCASE(LEFT(ri.fish_type,1)), SUBSTRING(ri.fish_type,2))
            ELSE 'Ikan Laut'
        END AS fish_name,
        NULLIF(TRIM(ri.fish_size),'') AS fish_size,
        COALESCE(ri.fish_weight,0) AS fish_weight,
        COALESCE(fs.weight_unit, ds.weight_unit, 'ons') AS fish_weight_unit,
        m.name,
        m.serving_type,
        SUM(ri.quantity) AS menu_total
    FROM reservation_items ri
    JOIN menus m ON m.id = ri.menu_id
    LEFT JOIN fish_stock fs ON fs.id = ri.fish_stock_ref_id
    LEFT JOIN daily_item_stock ds ON ds.id = ri.special_stock_ref_id
    JOIN reservations r ON r.id = ri.reservation_id
    WHERE DATE(r.reservation_datetime) = %s
    AND (
        m.category IN ('ikan nila','ikan laut')
        OR COALESCE(NULLIF(TRIM(ri.fish_size),''),'') <> ''
        OR COALESCE(NULLIF(TRIM(ri.fish_type),''),'') <> ''
        OR COALESCE(ri.fish_weight,0) > 0
    )
    GROUP BY
        CASE
            WHEN m.divisi IN ('local','bakar/local') THEN 'local'
            WHEN m.divisi IN ('seafood','bakar/seafood') THEN 'seafood'
            ELSE m.divisi
        END,
        CASE
            WHEN LOWER(TRIM(COALESCE(ri.fish_type,''))) = 'rahang tuna' THEN 'Rahang Tuna PCS'
            WHEN COALESCE(NULLIF(TRIM(ri.fish_size),''),'') <> '' THEN 'Nila'
            WHEN COALESCE(NULLIF(TRIM(ri.fish_type),''),'') <> '' THEN CONCAT(UCASE(LEFT(ri.fish_type,1)), SUBSTRING(ri.fish_type,2))
            ELSE 'Ikan Laut'
        END,
        NULLIF(TRIM(ri.fish_size),''),
        COALESCE(ri.fish_weight,0),
        COALESCE(fs.weight_unit, ds.weight_unit, 'ons'),
        m.name,
        m.serving_type
    ORDER BY fish_divisi, fish_name, fish_size, fish_weight, m.name, m.serving_type
    """,
        (selected_date,),
    )

    grouped_rows = OrderedDict()
    for row in cursor.fetchall():
        group_key = (row["fish_divisi"], row["fish_name"], row["fish_size"], row["fish_weight"], row["fish_weight_unit"])

        if group_key not in grouped_rows:
            grouped_rows[group_key] = {
                "fish_divisi": row["fish_divisi"],
                "fish_name": row["fish_name"],
                "fish_size": row["fish_size"],
                "fish_weight": row["fish_weight"],
                "fish_weight_unit": row["fish_weight_unit"],
                "total": 0,
                "menu_totals": OrderedDict(),
            }

        menu_label = format_menu_label(row.get("name"), row.get("serving_type"))
        menu_total = to_int_qty(row.get("menu_total"))
        grouped_rows[group_key]["total"] += menu_total
        grouped_rows[group_key]["menu_totals"][menu_label] = grouped_rows[group_key]["menu_totals"].get(menu_label, 0) + menu_total

    rows = list(grouped_rows.values())
    for row in rows:
        row["fish_weight_display"] = format_weight_display(row["fish_weight"], row.get("fish_weight_unit"))
        row["menu_names"] = "\n".join(f"{menu_name} ({menu_total})" for menu_name, menu_total in row["menu_totals"].items()) or "-"
    return rows
