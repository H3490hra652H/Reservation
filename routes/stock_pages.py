from datetime import date

from flask import redirect, render_template, request, url_for
from flask_login import current_user

from auth import admin_required, role_required
from db import get_db_connection
from services.common import effective_stock_status, format_weight_display, normalize_weight_to_ons, row_value, status_indicator
from services.history import log_stock_history
from services.menu_options import OPTION_STOCK_LABELS, get_latest_menu_status_map, get_latest_nila_status_map, get_latest_option_stock_map, get_latest_sea_fish_stock_rows
from services.stock import (
    PACKAGE_TUNA_MENU_NAMES,
    SPECIAL_TUNA_MENU_NAMES,
    apply_special_stock_statuses,
    ensure_additional_stock_tables,
    get_special_tuna_stock_context,
)


def _build_stock_overview_context(selected_date):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        _, _, special_tuna_stock = get_special_tuna_stock_context(cursor, selected_date)
        latest_menu_status_map = get_latest_menu_status_map(cursor, selected_date)
        latest_nila_status_map = get_latest_nila_status_map(cursor, selected_date)

        cursor.execute("SELECT id, name FROM menus ORDER BY name")
        stock_today = []
        for menu_row in cursor.fetchall():
            latest_status_row = latest_menu_status_map.get(menu_row["id"])
            current_status = row_value(latest_status_row, "status", 1, "ready")
            if current_status in ("not_ready", "pending", "out"):
                stock_today.append({"name": menu_row["name"], "status": current_status})
        stock_today = [row for row in stock_today if (row.get("name") or "").strip().lower() not in SPECIAL_TUNA_MENU_NAMES]

        sea_fish_stock = [
            row
            for row in get_latest_sea_fish_stock_rows(cursor, selected_date)
            if float(row.get("weight_ons") or 0) > 0 or int(row.get("fish_count") or 0) > 0
        ]

        for fish in sea_fish_stock:
            fish["display_weight"] = format_weight_display(fish["weight_ons"], fish.get("weight_unit"))

        nila_stock = []
        for size in ["kecil", "sedang", "besar", "jumbo", "super_jumbo"]:
            current_status = row_value(latest_nila_status_map.get(size), "status", 2, "ready")
            nila_stock.append({"size_category": size, "status": current_status, "status_dot": status_indicator(current_status)})

        special_stock = []
        rahang_tuna_rows = []
        package_stock = special_tuna_stock.get("package_stock")
        if package_stock:
            special_stock.append(
                {
                    "name": "Paket Dada Tuna",
                    "available_qty": package_stock.get("available_qty", 0),
                    "status": package_stock.get("status", "ready"),
                    "status_dot": status_indicator(package_stock.get("status", "ready")),
                }
            )

        for row in special_tuna_stock.get("all_rows", []):
            if row.get("weight_ons") and float(row["weight_ons"]) > 0:
                rahang_tuna_rows.append(
                    {
                        "display_weight": format_weight_display(row["weight_ons"], row.get("weight_unit")),
                        "available_qty": row.get("available_qty", 0),
                        "status": row.get("status", "ready"),
                    }
                )

        package_status = effective_stock_status(
            package_stock.get("status") if package_stock else "not_ready",
            package_stock.get("available_qty") if package_stock else 0,
        )
        if package_status != "ready":
            stock_today.append({"name": "Paket Dada Tuna", "status": package_status})

        rahang_summary = special_tuna_stock.get("summary") or {}
        if effective_stock_status(rahang_summary.get("status"), rahang_summary.get("available_qty")) != "ready":
            stock_today.append(
                {
                    "name": "Rahang Tuna",
                    "status": effective_stock_status(rahang_summary.get("status"), rahang_summary.get("available_qty")),
                }
            )

        return {
            "selected_date": selected_date,
            "stock_today": stock_today,
            "sea_fish_stock": sea_fish_stock,
            "nila_stock": nila_stock,
            "special_stock": special_stock,
            "rahang_tuna_rows": rahang_tuna_rows,
            "rahang_tuna_summary": rahang_summary,
        }
    finally:
        cursor.close()
        conn.close()


def register_stock_routes(app):
    @app.route("/stock")
    @role_required("admin", "kitchen")
    def stock_overview():
        selected_date = request.args.get("date") or date.today().strftime("%Y-%m-%d")
        return render_template(
            "stock.html",
            **_build_stock_overview_context(selected_date)
        )

    @app.route("/update_stock", methods=["GET","POST"])
    @admin_required
    def update_stock():
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        ensure_additional_stock_tables(cursor)

        selected_date = request.args.get("date")

        if not selected_date:
            selected_date = date.today().strftime("%Y-%m-%d")
        latest_menu_status_map = get_latest_menu_status_map(cursor, selected_date)
        latest_nila_status_map = get_latest_nila_status_map(cursor, selected_date)
        option_stock_map = get_latest_option_stock_map(cursor, selected_date)

        cursor.execute("""
            SELECT
                m.id,
                m.name,
                m.category,
                CASE
                    WHEN LOWER(m.name) = 'rahang tuna' THEN 'tuna_weight'
                    WHEN LOWER(m.name) IN ('dada tuna goreng','dada tuna bakar','paket dada tuna goreng','paket dada tuna bakar') THEN 'menu_piece'
                    ELSE m.stock_type
                END AS stock_source,
                'ready' AS status
            FROM menus m
            ORDER BY m.category, m.name
        """)
        menus = cursor.fetchall()
        for menu in menus:
            latest_status_row = latest_menu_status_map.get(menu["id"])
            if latest_status_row:
                menu["status"] = row_value(latest_status_row, "status", 1, "ready") or "ready"

        tuna_stock_menus, tuna_piece_stock, rahang_tuna_stock = get_special_tuna_stock_context(cursor, selected_date)
        apply_special_stock_statuses(menus, tuna_piece_stock, rahang_tuna_stock)
        actor_name = getattr(current_user, "id", "system")

        if request.method == "POST":
            for m in menus:
                menu_name = (m.get("name") or "").strip().lower()
                stock_source = m.get("stock_source")
                if stock_source in ("menu_piece", "tuna_weight") or menu_name in SPECIAL_TUNA_MENU_NAMES:
                    continue

                new_status = request.form.get(f"status_{m['id']}")
                if new_status is None:
                    continue

                previous_status = m.get("status", "ready")

                cursor.execute("""
                    INSERT INTO daily_menu_stock (menu_id, status, stock_date)
                    VALUES (%s,%s,%s)
                    ON DUPLICATE KEY UPDATE status=%s
                """,(m["id"], new_status, selected_date, new_status))
                log_stock_history(cursor, "menu_status", m["name"], previous_status, new_status, actor=actor_name)

            for stock_menu in tuna_stock_menus:
                qty_value = request.form.get(f"piece_qty_{stock_menu['id']}", "").strip()
                status_value = request.form.get(f"piece_status_{stock_menu['id']}", "ready")
                qty_number = int(qty_value) if qty_value else 0
                status_value = effective_stock_status(status_value, qty_number)
                current_piece_stock = tuna_piece_stock.get(stock_menu["id"], {})

                cursor.execute("""
                    INSERT INTO daily_item_stock (menu_id, stock_date, weight_ons, available_qty, status)
                    VALUES (%s,%s,0,%s,%s)
                    ON DUPLICATE KEY UPDATE available_qty=%s, status=%s
                """,(stock_menu["id"], selected_date, qty_number, status_value, qty_number, status_value))
                log_stock_history(
                    cursor,
                    "special_stock_qty",
                    "Paket Dada Tuna",
                    current_piece_stock.get("available_qty"),
                    qty_number,
                    actor=actor_name
                )
                log_stock_history(
                    cursor,
                    "special_stock_status",
                    "Paket Dada Tuna",
                    current_piece_stock.get("status"),
                    status_value,
                    actor=actor_name
                )

                for package_menu_name in PACKAGE_TUNA_MENU_NAMES:
                    cursor.execute("""
                        INSERT INTO daily_menu_stock (menu_id, status, stock_date)
                        SELECT id, %s, %s
                        FROM menus
                        WHERE LOWER(name) = %s
                        ON DUPLICATE KEY UPDATE status = VALUES(status)
                    """,(status_value, selected_date, package_menu_name))

            nila_sizes = ["kecil","sedang","besar","jumbo","super_jumbo"]
            for size in nila_sizes:
                status = request.form.get(f"nila_status_{size}")
                if not status:
                    continue
                existing = latest_nila_status_map.get(size)
                cursor.execute("""
                    SELECT id
                    FROM fish_stock
                    WHERE fish_type_id = 4
                    AND size_category = %s
                    AND stock_date = %s
                    ORDER BY id DESC
                    LIMIT 1
                """,(size, selected_date))
                current_date_row = cursor.fetchone()
                if current_date_row:
                    cursor.execute("""
                        UPDATE fish_stock
                        SET status = %s
                        WHERE id = %s
                    """,(status, current_date_row["id"]))
                else:
                    cursor.execute("""
                        INSERT INTO fish_stock
                        (fish_type_id,size_category,status,stock_date)
                        VALUES (4,%s,%s,%s)
                    """,(size,status,selected_date))
                log_stock_history(
                    cursor,
                    "nila_status",
                    f"Nila {size}",
                    row_value(existing, "status", 2, "ready"),
                    status,
                    actor=actor_name
                )

            for option_key, option_values in OPTION_STOCK_LABELS.items():
                for option_value, option_label in option_values.items():
                    option_status = request.form.get(f"option_stock_{option_key}_{option_value}")
                    if not option_status:
                        continue

                    previous_status = option_stock_map.get((option_key, option_value), "ready")
                    cursor.execute("""
                        INSERT INTO menu_option_stock (option_key, option_value, status, stock_date)
                        VALUES (%s,%s,%s,%s)
                        ON DUPLICATE KEY UPDATE status = VALUES(status)
                    """,(option_key, option_value, option_status, selected_date))
                    log_stock_history(
                        cursor,
                        "menu_option",
                        f"{option_key}:{option_label}",
                        previous_status,
                        option_status,
                        actor=actor_name
                    )

            conn.commit()
            cursor.close()
            conn.close()
            return redirect(f"/update_stock?date={selected_date}")

        fish_stock_today = [
            row
            for row in get_latest_sea_fish_stock_rows(cursor, selected_date)
            if float(row.get("weight_ons") or 0) > 0 or int(row.get("fish_count") or 0) > 0
        ]

        for fish in fish_stock_today:
            fish["display_weight"] = format_weight_display(fish["weight_ons"], fish.get("weight_unit"))

        nila_status = {
            size_key: row_value(latest_nila_status_map.get(size_key), "status", 2, "ready")
            for size_key in ["kecil","sedang","besar","jumbo","super_jumbo"]
        }
        nila_indicator = {}
        for s in ["kecil","sedang","besar","jumbo","super_jumbo"]:
            nila_status.setdefault(s,"ready")
            nila_indicator[s] = status_indicator(nila_status[s])

        tuna_piece_stock_by_menu = {}
        for stock_menu in tuna_stock_menus:
            tuna_piece_stock_by_menu[stock_menu["id"]] = tuna_piece_stock.get(stock_menu["id"], {
                "available_qty": 0,
                "status": "not_ready",
                "display_name": "Paket Dada Tuna",
                "status_dot": status_indicator("not_ready")
            })

        rahang_tuna_rows = []
        for row in rahang_tuna_stock.get("all_rows", []):
            if row.get("weight_ons") and float(row["weight_ons"]) > 0:
                row["display_weight"] = format_weight_display(row["weight_ons"], row.get("weight_unit"))
                rahang_tuna_rows.append(row)

        option_stock_rows = []
        for option_key, option_values in OPTION_STOCK_LABELS.items():
            option_group_label = "Bumbu Taiwan Snack" if option_key == "seasoning" else "Topping Taiwan Snack"
            for option_value, option_label in option_values.items():
                current_status = option_stock_map.get((option_key, option_value), "ready")
                option_stock_rows.append({
                    "group_label": option_group_label,
                    "option_key": option_key,
                    "option_value": option_value,
                    "option_label": option_label,
                    "status": current_status
                })

        cursor.close()
        conn.close()

        return render_template(
            "update_stock.html",
            menus=menus,
            fish_stock_today=fish_stock_today,
            nila_status=nila_status,
            nila_indicator=nila_indicator,
            tuna_stock_menus=tuna_stock_menus,
            tuna_piece_stock=tuna_piece_stock_by_menu,
            rahang_tuna_rows=rahang_tuna_rows,
            rahang_tuna_summary=rahang_tuna_stock.get("summary", {}),
            option_stock_rows=option_stock_rows,
            selected_date=selected_date
        )


    #================== CLEAR FISH STOCK =================
    @app.route("/clear_fish_stock")
    @admin_required
    def clear_fish_stock():

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
        DELETE FROM fish_stock
        WHERE stock_date = CURDATE()
        """)

        conn.commit()

        cursor.close()
        conn.close()

        return redirect("/update_stock")


    #================== FISH STOCK =================
    @app.route("/fish_stock", methods=["GET","POST"])
    @admin_required
    def fish_stock():
        selected_date = request.values.get("date")

        if not selected_date:
            selected_date = date.today().strftime("%Y-%m-%d")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        ensure_additional_stock_tables(cursor)
        _, _, rahang_tuna_stock = get_special_tuna_stock_context(cursor, selected_date)
        rahang_menu = rahang_tuna_stock.get("menu")

        if request.method == "POST":
            stock_kind = request.form.get("stock_kind", "sea")

            if stock_kind == "sea":
                fish_type_id = request.form.get("fish_type_id")
                weight_unit = request.form.get("weight_unit", "ons")
                weight = normalize_weight_to_ons(request.form.get("weight_ons"), weight_unit)
                count = request.form.get("fish_count") or 0
                status = request.form.get("status", "ready")

                if fish_type_id:
                    cursor.execute("""
                    INSERT INTO fish_stock
                    (fish_type_id, weight_ons, weight_unit, fish_count, status, stock_date)
                    VALUES (%s,%s,%s,%s,%s,%s)
                    """,(fish_type_id, weight, weight_unit, count, status, selected_date))

            elif stock_kind == "rahang_tuna" and rahang_menu:
                weight_unit = request.form.get("rahang_weight_unit", "ons")
                weight = normalize_weight_to_ons(request.form.get("rahang_weight"), weight_unit)
                qty = request.form.get("rahang_qty") or 0
                status = request.form.get("rahang_status", "ready")

                cursor.execute("""
                    INSERT INTO daily_item_stock (menu_id, stock_date, weight_ons, weight_unit, available_qty, status)
                    VALUES (%s,%s,%s,%s,%s,%s)
                    ON DUPLICATE KEY UPDATE available_qty=%s, status=%s, weight_unit=%s
                """,(rahang_menu["id"], selected_date, weight, weight_unit, qty, status, qty, status, weight_unit))

            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for("fish_stock", date=selected_date))

        cursor.execute("""
            SELECT
                id,
                name
            FROM fish_types ft
            WHERE ft.fish_category = 'sea'
            ORDER BY ft.name
        """)
        sea_fish_inputs = cursor.fetchall()

        fish_stock_today = get_latest_sea_fish_stock_rows(cursor, selected_date)

        for fish in fish_stock_today:
            fish["display_weight"] = format_weight_display(fish["weight_ons"], fish.get("weight_unit"))

        rahang_stock_rows = list(rahang_tuna_stock.get("all_rows", [])) if rahang_menu else []

        for item in rahang_stock_rows:
            item["display_weight"] = format_weight_display(item["weight_ons"], item.get("weight_unit"))

        cursor.close()
        conn.close()

        return render_template(
            "fish_stock.html",
            fish_stock_today=fish_stock_today,
            sea_fish_inputs=sea_fish_inputs,
            rahang_tuna_stock=rahang_stock_rows,
            rahang_tuna_summary=rahang_tuna_stock.get("summary", {}),
            rahang_menu=rahang_menu,
            selected_date=selected_date
        )


    @app.route("/fish_stock/update/<int:stock_id>", methods=["POST"])
    @admin_required
    def update_fish_stock_entry(stock_id):

        selected_date = request.form.get("date") or date.today().strftime("%Y-%m-%d")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
        UPDATE fish_stock
        SET weight_ons=%s,
            weight_unit=%s,
            fish_count=%s,
            status=%s
        WHERE id=%s
        """,(
            normalize_weight_to_ons(request.form.get("weight_ons"), request.form.get("weight_unit", "ons")),
            request.form.get("weight_unit", "ons"),
            request.form.get("fish_count"),
            request.form.get("status", "ready"),
            stock_id
        ))

        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for("fish_stock", date=selected_date))


    @app.route("/fish_stock/delete/<int:stock_id>")
    @admin_required
    def delete_fish_stock_entry(stock_id):

        selected_date = request.args.get("date") or date.today().strftime("%Y-%m-%d")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM fish_stock WHERE id=%s",(stock_id,))
        conn.commit()

        cursor.close()
        conn.close()

        return redirect(url_for("fish_stock", date=selected_date))


    @app.route("/tuna_stock/update/<int:stock_id>", methods=["POST"])
    @admin_required
    def update_tuna_stock_entry(stock_id):

        selected_date = request.form.get("date") or date.today().strftime("%Y-%m-%d")

        conn = get_db_connection()
        cursor = conn.cursor()
        ensure_additional_stock_tables(cursor)

        cursor.execute("""
        UPDATE daily_item_stock
        SET weight_ons=%s,
            weight_unit=%s,
            available_qty=%s,
            status=%s
        WHERE id=%s
        """,(
            normalize_weight_to_ons(request.form.get("weight_ons", 0), request.form.get("weight_unit", "ons")),
            request.form.get("weight_unit", "ons"),
            request.form.get("available_qty", 0),
            request.form.get("status", "ready"),
            stock_id
        ))

        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for("fish_stock", date=selected_date))


    @app.route("/tuna_stock/delete/<int:stock_id>")
    @admin_required
    def delete_tuna_stock_entry(stock_id):

        selected_date = request.args.get("date") or date.today().strftime("%Y-%m-%d")

        conn = get_db_connection()
        cursor = conn.cursor()
        ensure_additional_stock_tables(cursor)

        cursor.execute("DELETE FROM daily_item_stock WHERE id=%s",(stock_id,))
        conn.commit()

        cursor.close()
        conn.close()

        return redirect(url_for("fish_stock", date=selected_date))


    @app.route("/save_fish_stock", methods=["POST"])
    @admin_required
    def save_fish_stock():

        data = request.get_json()

        conn = get_db_connection()
        cursor = conn.cursor()

        for f in data["fish"]:

            if not f["weight"] or not f["count"]:
                continue

            cursor.execute("""
            INSERT INTO fish_stock
            (fish_type_id, weight_ons, fish_count, status, stock_date)
            VALUES (
                (SELECT id FROM fish_types WHERE name=%s),
                %s,
                %s,
                'ready',
                CURDATE()
            )
            """,(f["name"], f["weight"], f["count"]))

        conn.commit()

        cursor.close()
        conn.close()

        return {"status":"ok"}


    @app.route("/stock_history")
    @admin_required
    def stock_history():
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        ensure_additional_stock_tables(cursor)
        cursor.execute("""
            SELECT id, stock_scope, target_name, previous_value, new_value, actor_name, notes, created_at
            FROM stock_change_log
            ORDER BY created_at DESC, id DESC
            LIMIT 300
        """)
        history_rows = cursor.fetchall()
        cursor.close()
        conn.close()

        return render_template("stock_history.html", history_rows=history_rows)
