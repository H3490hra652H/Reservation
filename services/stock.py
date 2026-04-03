from services.common import (
    effective_stock_status,
    format_weight_display,
    normalize_weight_to_ons,
    row_value,
    status_indicator,
)
from services.menu_options import (
    apply_option_stock_to_catalog,
    build_display_menu_catalog,
    ensure_menu_catalog_updates,
    get_latest_daily_item_stock_rows,
    get_latest_menu_status_map,
    get_latest_nila_status_map,
    get_latest_option_stock_map,
    get_latest_sea_fish_stock_rows,
    validate_menu_option_stock,
)


PACKAGE_TUNA_MENU_NAMES = (
    "dada tuna goreng",
    "dada tuna bakar",
    "paket dada tuna goreng",
    "paket dada tuna bakar",
)
SPECIAL_TUNA_MENU_NAMES = PACKAGE_TUNA_MENU_NAMES + ("rahang tuna",)


def apply_special_stock_statuses(menus, piece_stock_map, special_tuna_stock):
    package_stock = special_tuna_stock.get("package_stock") or {}
    package_status = effective_stock_status(package_stock.get("status"), package_stock.get("available_qty"))

    rahang_summary = special_tuna_stock.get("summary") or {}
    rahang_status = effective_stock_status(rahang_summary.get("status"), rahang_summary.get("available_qty"))

    for menu in menus:
        menu_name = (menu.get("name") or "").strip().lower()
        stock_source = menu.get("stock_source")

        if (stock_source == "menu_piece" and menu.get("id") in piece_stock_map) or menu_name in PACKAGE_TUNA_MENU_NAMES:
            menu["status"] = package_status
        elif stock_source == "tuna_weight" or menu_name == "rahang tuna":
            menu["status"] = rahang_status


def get_stock_context(cursor, selected_date):
    ensure_additional_stock_tables(cursor)
    ensure_menu_catalog_updates(cursor)
    latest_menu_status_map = get_latest_menu_status_map(cursor, selected_date)

    cursor.execute(
        """
    SELECT
        m.id,
        m.name,
        m.serving_type,
        m.category,
        m.divisi,
        m.price,
        m.stock_type,
        CASE
            WHEN LOWER(m.name) = 'rahang tuna' THEN 'tuna_weight'
            WHEN LOWER(m.name) IN ('dada tuna goreng','dada tuna bakar','paket dada tuna goreng','paket dada tuna bakar') THEN 'menu_piece'
            ELSE m.stock_type
        END AS stock_source,
        'ready' AS status
    FROM menus m
    ORDER BY m.name
    """
    )
    menus = cursor.fetchall()

    for menu in menus:
        latest_status_row = latest_menu_status_map.get(menu["id"])
        if latest_status_row:
            menu["status"] = row_value(latest_status_row, "status", 1, "ready") or "ready"

    latest_nila_status_map = get_latest_nila_status_map(cursor, selected_date)
    nila_sizes = [
        {"size_category": size_key}
        for size_key in ["kecil", "sedang", "besar", "jumbo", "super_jumbo"]
        if effective_stock_status(row_value(latest_nila_status_map.get(size_key), "status", 2, "ready")) == "ready"
    ]

    sea_fish = [
        row
        for row in get_latest_sea_fish_stock_rows(cursor, selected_date)
        if row.get("status") == "ready" and int(row.get("fish_count") or 0) > 0
    ]

    _, piece_stock_map, special_tuna_stock = get_special_tuna_stock_context(cursor, selected_date)
    apply_special_stock_statuses(menus, piece_stock_map, special_tuna_stock)

    option_stock_map = get_latest_option_stock_map(cursor, selected_date)
    display_catalog = build_display_menu_catalog(menus)
    apply_option_stock_to_catalog(display_catalog, option_stock_map)

    return display_catalog, nila_sizes, sea_fish


def ensure_additional_stock_tables(cursor):
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS daily_item_stock (
        id INT AUTO_INCREMENT PRIMARY KEY,
        menu_id INT NOT NULL,
        stock_date DATE NOT NULL,
        weight_ons DECIMAL(5,1) NOT NULL DEFAULT 0.0,
        weight_unit ENUM('ons','kg') DEFAULT 'ons',
        available_qty INT NOT NULL DEFAULT 0,
        status ENUM('ready','not_ready') DEFAULT 'ready',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        UNIQUE KEY uniq_menu_stock (menu_id, stock_date, weight_ons),
        CONSTRAINT fk_daily_item_stock_menu FOREIGN KEY (menu_id) REFERENCES menus(id) ON DELETE CASCADE
    )
    """
    )

    cursor.execute(
        """
    ALTER TABLE fish_stock
    ADD COLUMN IF NOT EXISTS weight_unit ENUM('ons','kg') DEFAULT 'ons'
    """
    )

    cursor.execute(
        """
    ALTER TABLE daily_item_stock
    ADD COLUMN IF NOT EXISTS weight_unit ENUM('ons','kg') DEFAULT 'ons'
    """
    )

    cursor.execute("SHOW COLUMNS FROM daily_menu_stock LIKE 'status'")
    daily_menu_status_column = cursor.fetchone()
    daily_menu_status_type = (row_value(daily_menu_status_column, "Type", 1, "") or "").lower()
    if daily_menu_status_type and ("not_ready" not in daily_menu_status_type or "'out'" in daily_menu_status_type):
        cursor.execute(
            """
        ALTER TABLE daily_menu_stock
        MODIFY COLUMN status ENUM('ready','pending','out','not_ready') DEFAULT 'ready'
        """
        )
        cursor.execute(
            """
        UPDATE daily_menu_stock
        SET status = 'not_ready'
        WHERE status IN ('out','')
        """
        )
        cursor.execute(
            """
        ALTER TABLE daily_menu_stock
        MODIFY COLUMN status ENUM('ready','pending','not_ready') DEFAULT 'ready'
        """
        )

    cursor.execute(
        """
    ALTER TABLE reservation_items
    ADD COLUMN IF NOT EXISTS fish_stock_ref_id INT NULL
    """
    )
    cursor.execute(
        """
    ALTER TABLE reservation_items
    ADD COLUMN IF NOT EXISTS special_stock_ref_id INT NULL
    """
    )
    cursor.execute(
        """
    ALTER TABLE reservation_items
    ADD COLUMN IF NOT EXISTS menu_options_json LONGTEXT NULL
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS menu_option_stock (
        id INT AUTO_INCREMENT PRIMARY KEY,
        option_key VARCHAR(80) NOT NULL,
        option_value VARCHAR(80) NOT NULL,
        status ENUM('ready','not_ready') NOT NULL DEFAULT 'ready',
        stock_date DATE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        UNIQUE KEY uniq_option_stock (option_key, option_value, stock_date)
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS stock_change_log (
        id INT AUTO_INCREMENT PRIMARY KEY,
        stock_scope VARCHAR(80) NOT NULL,
        target_name VARCHAR(255) NOT NULL,
        previous_value TEXT NULL,
        new_value TEXT NULL,
        actor_name VARCHAR(120) NULL,
        notes TEXT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS reservation_change_log (
        id INT AUTO_INCREMENT PRIMARY KEY,
        reservation_id INT NULL,
        reservation_item_id INT NULL,
        action_type VARCHAR(40) NOT NULL,
        change_scope VARCHAR(40) NOT NULL,
        summary TEXT NOT NULL,
        actor_name VARCHAR(120) NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    )

    ensure_menu_catalog_updates(cursor)


def get_special_tuna_stock_context(cursor, selected_date):
    ensure_additional_stock_tables(cursor)

    cursor.execute(
        """
    SELECT
        id,
        name,
        serving_type
    FROM menus
    WHERE LOWER(name) IN (
        'rahang tuna',
        'dada tuna goreng',
        'dada tuna bakar',
        'paket dada tuna goreng',
        'paket dada tuna bakar'
    )
    ORDER BY
        CASE
            WHEN LOWER(name) IN ('paket dada tuna goreng','paket dada tuna bakar') THEN 1
            WHEN LOWER(name) IN ('dada tuna goreng','dada tuna bakar') THEN 2
            WHEN LOWER(name) = 'rahang tuna' THEN 3
            ELSE 4
        END,
        name
    """
    )
    stock_menus = cursor.fetchall()

    if not stock_menus:
        return [], {}, {}

    menu_ids = [row["id"] for row in stock_menus]
    stock_rows = get_latest_daily_item_stock_rows(cursor, menu_ids, selected_date)

    package_menu = None
    rahang_menu = None
    package_rows = []
    ready_rahang_rows = []
    all_rahang_rows = []
    piece_stock_map = {}

    for stock_menu in stock_menus:
        name_key = stock_menu["name"].strip().lower()
        if name_key == "rahang tuna":
            rahang_menu = stock_menu
        elif package_menu is None and name_key in PACKAGE_TUNA_MENU_NAMES:
            package_menu = stock_menu

    for row in stock_rows:
        name_key = row["name"].strip().lower()
        row["status"] = effective_stock_status(row.get("status"), row.get("available_qty"))

        if name_key == "rahang tuna":
            row["display_weight"] = format_weight_display(row["weight_ons"], row.get("weight_unit"))
            row["label"] = f"Rahang Tuna - {row['display_weight']} ({row['available_qty']} stok)"
            all_rahang_rows.append(row)
            if row["weight_ons"] and row["available_qty"] > 0 and row["status"] == "ready":
                ready_rahang_rows.append(row)
        else:
            package_rows.append(row)

    package_stock = None
    if package_menu:
        package_stock = next((row for row in package_rows if row["menu_id"] == package_menu["id"]), None)
    if package_stock is None and package_rows:
        package_stock = package_rows[0]

    if package_stock:
        package_stock["display_name"] = "Paket Dada Tuna"
        package_stock["status_dot"] = status_indicator(package_stock["status"])

    for row in stock_rows:
        name_key = row["name"].strip().lower()
        if name_key != "rahang tuna" and package_stock:
            piece_stock_map[row["menu_id"]] = package_stock

    if package_stock:
        for stock_menu in stock_menus:
            if stock_menu["name"].strip().lower() in PACKAGE_TUNA_MENU_NAMES:
                piece_stock_map[stock_menu["id"]] = package_stock

    ready_rahang_total = sum(row["available_qty"] for row in ready_rahang_rows)
    rahang_status_row = next((row for row in all_rahang_rows if (row["weight_ons"] or 0) == 0 and row["status"] == "not_ready"), None)
    rahang_summary = {
        "display_name": "Rahang Tuna PCS",
        "available_qty": ready_rahang_total,
        "status": "ready" if ready_rahang_total > 0 else "not_ready",
        "status_dot": status_indicator("ready" if ready_rahang_total > 0 else "not_ready"),
        "source_count": len(ready_rahang_rows),
        "has_marker": bool(rahang_status_row),
    }
    if ready_rahang_total <= 0 and rahang_status_row:
        rahang_summary["status"] = "not_ready"
        rahang_summary["status_dot"] = status_indicator("not_ready")

    filtered_stock_menus = [package_menu] if package_menu else []

    return filtered_stock_menus, piece_stock_map, {
        "menu": rahang_menu,
        "rows": ready_rahang_rows,
        "all_rows": all_rahang_rows,
        "summary": rahang_summary,
        "package_stock": package_stock,
    }


def reduce_stock_after_order(cursor, fish_stock_id=None, special_stock_id=None, qty=0):
    if qty <= 0:
        return

    if fish_stock_id:
        cursor.execute(
            """
        UPDATE fish_stock
        SET fish_count = GREATEST(fish_count - %s, 0)
        WHERE id = %s
        """,
            (qty, fish_stock_id),
        )

    if special_stock_id:
        cursor.execute(
            """
        UPDATE daily_item_stock
        SET available_qty = GREATEST(available_qty - %s, 0)
        WHERE id = %s
        """,
            (qty, special_stock_id),
        )


def resolve_package_stock_row(cursor, stock_date):
    placeholders = ",".join(["%s"] * len(PACKAGE_TUNA_MENU_NAMES))
    cursor.execute(
        f"""
        SELECT
            ds.id,
            ds.menu_id,
            ds.available_qty,
            ds.status
        FROM daily_item_stock ds
        JOIN menus m ON m.id = ds.menu_id
        WHERE ds.stock_date <= %s
        AND LOWER(m.name) IN ({placeholders})
        AND COALESCE(ds.weight_ons, 0) = 0
        ORDER BY
            ds.stock_date DESC,
            CASE WHEN ds.status = 'ready' AND ds.available_qty > 0 THEN 0 ELSE 1 END,
            ds.id
        LIMIT 1
        """,
        [stock_date] + list(PACKAGE_TUNA_MENU_NAMES),
    )
    row = cursor.fetchone()
    if row and effective_stock_status(row_value(row, "status", 3), row_value(row, "available_qty", 2)) == "ready":
        return row
    return None


def resolve_selected_stock_refs(cursor, reservation_date, menu_id, fish_type=None, fish_weight=None, fish_stock_id=None, special_stock_id=None):
    resolved_fish_stock_id = int(fish_stock_id) if fish_stock_id else None
    resolved_special_stock_id = int(special_stock_id) if special_stock_id else None

    if not reservation_date:
        return resolved_fish_stock_id, resolved_special_stock_id

    normalized_fish_type = (fish_type or "").strip().lower()
    normalized_weight = fish_weight

    if not resolved_special_stock_id:
        cursor.execute("SELECT LOWER(name) AS name FROM menus WHERE id = %s", (menu_id,))
        selected_menu = cursor.fetchone()
        menu_name = str(row_value(selected_menu, "name", 0, "")).strip().lower()

        if menu_name in PACKAGE_TUNA_MENU_NAMES:
            package_row = resolve_package_stock_row(cursor, reservation_date)
            if package_row:
                resolved_special_stock_id = row_value(package_row, "id", 0)

    if not resolved_special_stock_id and normalized_fish_type == "rahang tuna" and normalized_weight not in (None, "", "0", "0.0"):
        cursor.execute(
            """
        SELECT ds.id
        FROM daily_item_stock ds
        JOIN menus m ON m.id = ds.menu_id
        WHERE ds.stock_date <= %s
        AND LOWER(m.name) = 'rahang tuna'
        AND ds.weight_ons = %s
        ORDER BY ds.stock_date DESC, ds.id DESC
        LIMIT 1
        """,
            (reservation_date, normalized_weight),
        )
        row = cursor.fetchone()
        if row:
            resolved_special_stock_id = row_value(row, "id", 0)

    if not resolved_fish_stock_id and normalized_fish_type and normalized_fish_type != "rahang tuna" and normalized_weight not in (None, "", "0", "0.0"):
        cursor.execute(
            """
        SELECT fs.id
        FROM fish_stock fs
        JOIN fish_types ft ON ft.id = fs.fish_type_id
        WHERE fs.stock_date <= %s
        AND LOWER(ft.name) = %s
        AND fs.weight_ons = %s
        ORDER BY fs.stock_date DESC, fs.id DESC
        LIMIT 1
        """,
            (reservation_date, normalized_fish_type, normalized_weight),
        )
        row = cursor.fetchone()
        if row:
            resolved_fish_stock_id = row_value(row, "id", 0)

    return resolved_fish_stock_id, resolved_special_stock_id


def resolve_item_stock_refs(cursor, item):
    fish_stock_id = item.get("fish_stock_ref_id")
    special_stock_id = item.get("special_stock_ref_id")

    if fish_stock_id or special_stock_id:
        return fish_stock_id, special_stock_id

    reservation_date = item.get("reservation_date")
    fish_type = (item.get("fish_type") or "").strip().lower()
    fish_weight = item.get("fish_weight") or 0
    menu_name = (item.get("name") or "").strip().lower()

    if not reservation_date:
        return None, None

    if fish_type and fish_weight and fish_type != "none":
        if fish_type == "rahang tuna":
            cursor.execute(
                """
            SELECT ds.id
            FROM daily_item_stock ds
            JOIN menus m ON m.id = ds.menu_id
            WHERE ds.stock_date <= %s
            AND LOWER(m.name) = 'rahang tuna'
            AND ds.weight_ons = %s
            ORDER BY ds.stock_date DESC, ds.id DESC
            LIMIT 1
            """,
                (reservation_date, fish_weight),
            )
            row = cursor.fetchone()
            return None, row_value(row, "id", 0) if row else None

        cursor.execute(
            """
        SELECT fs.id
        FROM fish_stock fs
        JOIN fish_types ft ON ft.id = fs.fish_type_id
        WHERE fs.stock_date <= %s
        AND LOWER(ft.name) = %s
        AND fs.weight_ons = %s
        ORDER BY fs.stock_date DESC, fs.id DESC
        LIMIT 1
        """,
            (reservation_date, fish_type, fish_weight),
        )
        row = cursor.fetchone()
        return row_value(row, "id", 0) if row else None, None

    if menu_name in PACKAGE_TUNA_MENU_NAMES:
        placeholders = ",".join(["%s"] * len(PACKAGE_TUNA_MENU_NAMES))
        cursor.execute(
            f"""
            SELECT ds.id
            FROM daily_item_stock ds
            JOIN menus m ON m.id = ds.menu_id
            WHERE ds.stock_date <= %s
            AND LOWER(m.name) IN ({placeholders})
            AND COALESCE(ds.weight_ons, 0) = 0
            ORDER BY ds.stock_date DESC, ds.id DESC
            LIMIT 1
            """,
            [reservation_date] + list(PACKAGE_TUNA_MENU_NAMES),
        )
        row = cursor.fetchone()
        return None, row_value(row, "id", 0) if row else None

    return None, None


def validate_stock_request(cursor, reservation_date, menu_id, qty, fish_type=None, fish_size=None, fish_weight=None, fish_stock_id=None, special_stock_id=None, current_item=None, menu_options_json=None):
    try:
        qty = int(qty)
    except (TypeError, ValueError):
        return False, "Jumlah menu tidak valid."

    if qty <= 0:
        return False, "Jumlah menu harus lebih dari 0."

    is_option_ready, option_message = validate_menu_option_stock(cursor, reservation_date, menu_options_json)
    if not is_option_ready:
        return False, option_message

    cursor.execute(
        """
    SELECT
        LOWER(name) AS name,
        CASE
            WHEN LOWER(name) = 'rahang tuna' THEN 'tuna_weight'
            WHEN LOWER(name) IN ('dada tuna goreng','dada tuna bakar','paket dada tuna goreng','paket dada tuna bakar') THEN 'menu_piece'
            ELSE stock_type
        END AS stock_source
    FROM menus
    WHERE id = %s
    """,
        (menu_id,),
    )
    menu_row = cursor.fetchone()

    if not menu_row:
        return False, "Menu tidak ditemukan."

    stock_source = row_value(menu_row, "stock_source", 1)
    menu_name = str(row_value(menu_row, "name", 0, "")).strip().lower()
    current_qty = int(current_item.get("quantity") or 0) if current_item else 0
    current_fish_ref = current_item.get("fish_stock_ref_id") if current_item else None
    current_special_ref = current_item.get("special_stock_ref_id") if current_item else None

    if stock_source == "size":
        if not fish_size:
            return False, "Ukuran Nila belum dipilih."

        nila_row = get_latest_nila_status_map(cursor, reservation_date).get(fish_size)
        nila_status = row_value(nila_row, "status", 0, "not_ready")
        if effective_stock_status(nila_status) != "ready":
            return False, f"Stock Nila ukuran {fish_size} sedang tidak ready."
        return True, None

    if stock_source == "weight":
        if not fish_stock_id:
            return False, "Stock ikan laut belum dipilih."

        cursor.execute(
            """
        SELECT fish_count, status, stock_date
        FROM fish_stock
        WHERE id = %s
        LIMIT 1
        """,
            (fish_stock_id,),
        )
        stock_row = cursor.fetchone()
        if not stock_row:
            return False, "Stock ikan laut tidak ditemukan."

        available = int(row_value(stock_row, "fish_count", 0, 0) or 0)
        status = row_value(stock_row, "status", 1, "not_ready")

        if current_fish_ref and str(current_fish_ref) == str(fish_stock_id):
            available += current_qty

        if effective_stock_status(status, available) != "ready":
            return False, "Stock ikan laut sedang tidak ready."

        if qty > available:
            return False, f"Stock ikan laut hanya tersisa {available}."

        return True, None

    if stock_source in ("tuna_weight", "menu_piece"):
        if not special_stock_id:
            stock_label = "Rahang Tuna" if stock_source == "tuna_weight" or menu_name == "rahang tuna" else "Paket Dada Tuna"
            return False, f"Stock {stock_label} belum dipilih."

        cursor.execute(
            """
        SELECT available_qty, status, stock_date
        FROM daily_item_stock
        WHERE id = %s
        LIMIT 1
        """,
            (special_stock_id,),
        )
        stock_row = cursor.fetchone()
        if not stock_row:
            return False, "Stock item khusus tidak ditemukan."

        available = int(row_value(stock_row, "available_qty", 0, 0) or 0)
        status = row_value(stock_row, "status", 1, "not_ready")

        if current_special_ref and str(current_special_ref) == str(special_stock_id):
            available += current_qty

        if effective_stock_status(status, available) != "ready":
            label = "Rahang Tuna" if stock_source == "tuna_weight" or menu_name == "rahang tuna" else "Paket Dada Tuna"
            return False, f"Stock {label} sedang tidak ready."

        if qty > available:
            label = "Rahang Tuna" if stock_source == "tuna_weight" or menu_name == "rahang tuna" else "Paket Dada Tuna"
            return False, f"Stock {label} hanya tersisa {available}."

    return True, None


def restore_stock_for_item(cursor, item):
    qty = int(item.get("quantity") or 0)
    if qty <= 0:
        return

    fish_stock_id = item.get("fish_stock_ref_id")
    special_stock_id = item.get("special_stock_ref_id")

    if not fish_stock_id and not special_stock_id:
        return

    if fish_stock_id:
        cursor.execute(
            """
        UPDATE fish_stock
        SET fish_count = fish_count + %s
        WHERE id = %s
        """,
            (qty, fish_stock_id),
        )

    if special_stock_id:
        cursor.execute(
            """
        UPDATE daily_item_stock
        SET available_qty = available_qty + %s
        WHERE id = %s
        """,
            (qty, special_stock_id),
        )
