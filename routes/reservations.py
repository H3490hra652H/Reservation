from datetime import date, datetime

from flask import redirect, render_template, request, url_for
from flask_login import current_user, login_required

from db import get_db_connection
from services.common import dish_description_sql, format_currency, format_fish_info, format_menu_label, format_weight_display, render_notice_page
from services.history import build_menu_history_summary, get_menu_label_for_history, log_reservation_history, prepare_reservation_history_rows
from services.menu_options import (
    build_menu_display_note,
    build_menu_display_note_from_row,
    build_menu_options_payload_from_form,
    build_option_summary_from_row,
    get_effective_selected_options,
    get_payload_display_name,
    resolve_menu_submission,
)
from services.stock import (
    ensure_additional_stock_tables,
    get_stock_context,
    get_special_tuna_stock_context,
    reduce_stock_after_order,
    resolve_selected_stock_refs,
    restore_stock_for_item,
    validate_stock_request,
)


def register_reservations_routes(app):
    @app.route("/create_reservation")
    @login_required
    def create_reservation():

        selected_date = request.args.get("date")

        if not selected_date:
            selected_date = date.today().strftime("%Y-%m-%d")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        menus, nila_sizes, sea_fish = get_stock_context(cursor, selected_date)
        tuna_stock_menus, tuna_piece_stock, rahang_tuna_stock = get_special_tuna_stock_context(cursor, selected_date)

        nila_size_options = [row["size_category"] for row in nila_sizes]

        for fish in sea_fish:
            fish["display_weight"] = format_weight_display(fish["weight_ons"], fish.get("weight_unit"))
            fish["label"] = f"{fish['name'].capitalize()} - {fish['display_weight']} ({fish['fish_count']} stok)"

        cursor.close()
        conn.close()

        return render_template(
            "create_reservation.html",
            menus=menus,
            nila_sizes=nila_size_options,
            sea_fish=sea_fish,
            tuna_piece_stock=tuna_piece_stock,
            rahang_tuna_stock=rahang_tuna_stock,
            selected_date=selected_date
        )


    # ================= ADD RESERVATION =================

    # ================= ADD RESERVATION =================

    @app.route("/add_reservation", methods=["POST"])
    @login_required
    def add_reservation():

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        ensure_additional_stock_tables(cursor)

        name = request.form["customer_name"]
        table = request.form["table_number"]
        people = request.form["people_count"]
        datetime_res = request.form["reservation_datetime"]
        description = request.form["description"]
        reservation_date = datetime_res.split("T")[0] if "T" in datetime_res else datetime_res.split(" ")[0]
    

        cursor.execute("""
            INSERT INTO reservations
            (customer_name, table_number, people_count, reservation_datetime, description)
            VALUES (%s,%s,%s,%s,%s)
        """,(name,table,people,datetime_res,description))

        reservation_id = cursor.lastrowid
        log_reservation_history(
            cursor,
            reservation_id,
            "create",
            "reservation",
            f"Reservasi dibuat untuk {name}, meja {table}, pax {people}.",
            actor=getattr(current_user, "id", "system")
        )

        menu_ids = request.form.getlist("menu_id[]")
        display_menu_ids = request.form.getlist("display_menu_id[]")
        fish_types = request.form.getlist("fish_type[]")
        fish_sizes = request.form.getlist("fish_size[]")
        fish_weights = request.form.getlist("fish_weight[]")
        fish_stock_ids = request.form.getlist("fish_stock_id[]")
        special_stock_ids = request.form.getlist("special_stock_id[]")
        qtys = request.form.getlist("qty[]")
        special_requests = request.form.getlist("special_request[]")
        dish_descriptions = request.form.getlist("dish_description[]")
        menu_options_json_list = request.form.getlist("menu_options_json[]")
        menu_catalog, _, _ = get_stock_context(cursor, reservation_date)

        for menu_id, display_menu_id, qty, special, dish_desc, menu_options_json, fish_type, size, weight, fish_stock_id, special_stock_id in zip(
    menu_ids, display_menu_ids, qtys, special_requests, dish_descriptions, menu_options_json_list, fish_types, fish_sizes, fish_weights, fish_stock_ids, special_stock_ids):

            resolved_menu_id = resolve_menu_submission(
                menu_catalog,
                menu_id,
                display_menu_id=display_menu_id,
                menu_options_json=menu_options_json
            )
            if resolved_menu_id is None:
                conn.rollback()
                cursor.close()
                conn.close()
                return render_notice_page(
                    "Menu Tidak Valid",
                    "Pilihan menu belum lengkap. Silakan pilih ulang menu yang ingin disimpan.",
                    back_url=url_for("create_reservation", date=reservation_date),
                    back_label="Kembali",
                    status_code=400
                )

            if special == "with_special":
                special_request = dish_desc
            else:
                special_request = None

            if fish_type in ("", "none"):
                fish_type = None

            if size == "":
                size = None

            if weight in ("", "0", "0.0"):
                weight = None

            resolved_fish_stock_id, resolved_special_stock_id = resolve_selected_stock_refs(
                cursor,
                reservation_date,
                resolved_menu_id,
                fish_type=fish_type,
                fish_weight=weight,
                fish_stock_id=fish_stock_id,
                special_stock_id=special_stock_id
            )

            is_valid_stock, stock_message = validate_stock_request(
                cursor,
                reservation_date,
                resolved_menu_id,
                qty,
                fish_type=fish_type,
                fish_size=size,
                fish_weight=weight,
                fish_stock_id=resolved_fish_stock_id,
                special_stock_id=resolved_special_stock_id,
                menu_options_json=menu_options_json
            )
            if not is_valid_stock:
                conn.rollback()
                cursor.close()
                conn.close()
                return render_notice_page(
                    "Stock Tidak Cukup",
                    stock_message,
                    back_url=url_for("create_reservation", date=reservation_date),
                    back_label="Kembali",
                    status_code=400
                )

            cursor.execute("""
                INSERT INTO reservation_items
                (reservation_id, menu_id, quantity,
                special_request, dish_description,
                fish_type, fish_size, fish_weight, fish_stock_ref_id, special_stock_ref_id, menu_options_json)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,(
                reservation_id,
                resolved_menu_id,
                qty,
                special_request,
                dish_desc,
                fish_type,
                size,
                weight,
                resolved_fish_stock_id,
                resolved_special_stock_id,
                menu_options_json or None
            ))
            log_reservation_history(
                cursor,
                reservation_id,
                "create",
                "menu",
                build_menu_history_summary(
                    "create",
                    get_menu_label_for_history(cursor, resolved_menu_id, menu_options_json=menu_options_json),
                    qty=qty,
                    note=build_menu_display_note(menu_options_json, dish_desc)
                ),
                actor=getattr(current_user, "id", "system"),
                reservation_item_id=cursor.lastrowid
            )

            reduce_stock_after_order(
                cursor,
                fish_stock_id=resolved_fish_stock_id,
                special_stock_id=resolved_special_stock_id,
                qty=int(qty)
            )

        conn.commit()

        cursor.close()
        conn.close()

        return redirect("/reservations")


    @app.route("/reservation_menu/<int:reservation_id>")
    @login_required
    def reservation_menu(reservation_id):
        search_query = (request.args.get("search") or "").strip()

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        description_expr = dish_description_sql("ri")

        cursor.execute("""
        SELECT
            id,
            customer_name,
            table_number,
            people_count,
            reservation_datetime,
            description
        FROM reservations
        WHERE id = %s
        """,(reservation_id,))
        reservation_info = cursor.fetchone()

        if not reservation_info:
            cursor.close()
            conn.close()
            return render_notice_page(
                "Reservasi Tidak Ditemukan",
                "Data reservasi yang Anda buka sudah tidak tersedia.",
                back_url=url_for("reservations"),
                back_label="Kembali ke List Reservasi"
            )

        reservation_back_date = ""
        reservation_datetime = reservation_info.get("reservation_datetime")
        if isinstance(reservation_datetime, datetime):
            reservation_back_date = reservation_datetime.strftime("%Y-%m-%d")
        elif reservation_datetime:
            reservation_back_date = str(reservation_datetime).split(" ")[0]

        query = """
        SELECT
            ri.id,
            ri.reservation_id,
            ri.quantity,
            ri.menu_options_json,
            ri.fish_type,
            ri.fish_size,
            ri.fish_weight,
            COALESCE(fs.weight_unit, ds.weight_unit, 'ons') AS fish_weight_unit,
        """ + description_expr + """ AS dish_description,
            m.name,
            m.serving_type,
            m.price
        FROM reservation_items ri
        JOIN menus m ON ri.menu_id = m.id
        LEFT JOIN fish_stock fs ON fs.id = ri.fish_stock_ref_id
        LEFT JOIN daily_item_stock ds ON ds.id = ri.special_stock_ref_id
        WHERE ri.reservation_id = %s
        """
        params = [reservation_id]

        if search_query:
            query += """
            AND (
                m.name LIKE %s
                OR m.serving_type LIKE %s
                OR COALESCE(NULLIF(TRIM(ri.fish_type),''),'') LIKE %s
                OR COALESCE(NULLIF(TRIM(ri.fish_size),''),'') LIKE %s
                OR COALESCE(""" + description_expr + """,'') LIKE %s
            )
            """
            search_like = f"%{search_query}%"
            params.extend([search_like] * 5)

        query += " ORDER BY ri.id DESC"
        cursor.execute(query, params)

        reservation_menus = cursor.fetchall()
        for item in reservation_menus:
            item["effective_selected_options"] = get_effective_selected_options(item)
            item["fish_info"] = format_fish_info(item)
            item["price_display"] = format_currency(item.get("price"))
            item["display_menu_name"] = format_menu_label(
                get_payload_display_name(
                    item.get("menu_options_json"),
                    item.get("name"),
                    item.get("serving_type")
                ),
                item.get("serving_type")
            )
            item["option_summary"] = build_option_summary_from_row(item)
            item["display_note"] = build_menu_display_note_from_row(item)

        cursor.close()
        conn.close()

        return render_template(
            "reservation_menu.html",
            reservation_menus=reservation_menus,
            reservation_id=reservation_id,
            reservation_info=reservation_info,
            reservation_back_date=reservation_back_date,
            search_query=search_query
        )
    # ================= RESERVATION LIST =================

    @app.route("/reservations")
    @login_required
    def reservations():

        selected_date = request.args.get("date")
        search_query = (request.args.get("search") or "").strip()

        if not selected_date:
            selected_date = datetime.now().strftime("%Y-%m-%d")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT id,customer_name,table_number,
                   people_count,reservation_datetime,description
            FROM reservations
            WHERE DATE(reservation_datetime) = %s
        """
        params = [selected_date]

        if search_query:
            query += """
            AND (
                CAST(id AS CHAR) LIKE %s
                OR customer_name LIKE %s
                OR table_number LIKE %s
                OR COALESCE(description,'') LIKE %s
            )
            """
            search_like = f"%{search_query}%"
            params.extend([search_like] * 4)

        query += " ORDER BY id DESC"
        cursor.execute(query, params)

        data = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template(
            "reservations.html",
            data=data,
            selected_date=selected_date,
            search_query=search_query
        )


    @app.route("/delete/<int:res_id>")
    @login_required
    def delete_reservation(res_id):

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        ensure_additional_stock_tables(cursor)

        cursor.execute("""
        SELECT
            ri.id,
            ri.reservation_id,
            ri.quantity,
            ri.fish_type,
            ri.fish_size,
            ri.fish_weight,
            ri.fish_stock_ref_id,
            ri.special_stock_ref_id,
            m.name,
            DATE_FORMAT(r.reservation_datetime, '%Y-%m-%d') AS reservation_date
        FROM reservation_items ri
        JOIN menus m ON m.id = ri.menu_id
        JOIN reservations r ON r.id = ri.reservation_id
        WHERE ri.reservation_id = %s
        """,(res_id,))
        items = cursor.fetchall()

        for item in items:
            restore_stock_for_item(cursor, item)

        log_reservation_history(
            cursor,
            res_id,
            "delete",
            "reservation",
            f"Reservasi dihapus bersama {len(items)} item menu.",
            actor=getattr(current_user, "id", "system")
        )

        cursor.execute("DELETE FROM reservations WHERE id=%s",(res_id,))
        conn.commit()

        cursor.close()
        conn.close()

        return redirect("/reservations")

    # ================= DELETE ALL RESERVATIONS =================

    @app.route("/delete_all_reservations")
    @login_required
    def delete_all_reservations():

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        ensure_additional_stock_tables(cursor)

        cursor.execute("""
        SELECT
            ri.id,
            ri.reservation_id,
            ri.quantity,
            ri.fish_type,
            ri.fish_size,
            ri.fish_weight,
            ri.fish_stock_ref_id,
            ri.special_stock_ref_id,
            m.name,
            DATE_FORMAT(r.reservation_datetime, '%Y-%m-%d') AS reservation_date
        FROM reservation_items ri
        JOIN menus m ON m.id = ri.menu_id
        JOIN reservations r ON r.id = ri.reservation_id
        """)
        items = cursor.fetchall()

        for item in items:
            restore_stock_for_item(cursor, item)

        cursor.execute("DELETE FROM reservation_items")
        cursor.execute("DELETE FROM reservations")

        conn.commit()

        cursor.close()
        conn.close()

        return redirect("/reservations")


    # ================= EDIT RESERVATION =================

    @app.route("/edit/<int:res_id>", methods=["GET","POST"])
    @login_required
    def edit_reservation(res_id):

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        if request.method == "POST":

            name = request.form["customer_name"]
            table = request.form["table_number"]
            people = request.form["people_count"]
            time = request.form["reservation_datetime"]
            deskripsi = request.form["description"]

            cursor.execute("SELECT * FROM reservations WHERE id=%s",(res_id,))
            existing_reservation = cursor.fetchone()

            cursor.execute("""
            UPDATE reservations
            SET customer_name=%s,
                table_number=%s,
                people_count=%s,
                reservation_datetime=%s,
                description=%s
            WHERE id=%s
            """,(name,table,people,time,deskripsi,res_id))

            if existing_reservation:
                log_reservation_history(
                    cursor,
                    res_id,
                    "update",
                    "reservation",
                    f"Reservasi diubah dari {existing_reservation.get('customer_name')} / meja {existing_reservation.get('table_number')} menjadi {name} / meja {table}.",
                    actor=getattr(current_user, "id", "system")
                )

            conn.commit()

            cursor.close()
            conn.close()

            return redirect("/reservations")

        cursor.execute("SELECT * FROM reservations WHERE id=%s",(res_id,))
        reservation = cursor.fetchone()

        if reservation and reservation.get("reservation_datetime"):
            reservation["reservation_datetime"] = reservation["reservation_datetime"].strftime("%Y-%m-%dT%H:%M")

        cursor.close()
        conn.close()

        return render_template("edit_reservation.html",reservation=reservation)

    #================== EDIT MENU =================
    @app.route("/edit_menu/<int:item_id>", methods=["GET","POST"])
    @login_required
    def edit_menu(item_id):

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        ensure_additional_stock_tables(cursor)

        # ================= AMBIL MENU YANG DIEDIT =================
        cursor.execute("""
            SELECT
                ri.id,
                ri.reservation_id,
                ri.menu_id,
                ri.quantity,
                ri.special_request,
                ri.dish_description,
                ri.menu_options_json,
                ri.fish_type,
                ri.fish_size,
                ri.fish_weight,
                ri.fish_stock_ref_id,
                ri.special_stock_ref_id,
                m.name,
                m.serving_type,
                DATE_FORMAT(r.reservation_datetime, '%Y-%m-%d') AS reservation_date
            FROM reservation_items ri
            JOIN menus m ON ri.menu_id = m.id
            JOIN reservations r ON r.id = ri.reservation_id
            WHERE ri.id = %s
        """,(item_id,))

        menu = cursor.fetchone()

        if not menu:
            cursor.close()
            conn.close()
            return render_notice_page(
                "Menu Tidak Ditemukan",
                "Menu yang ingin Anda edit sudah tidak ada. Silakan kembali ke halaman sebelumnya.",
                back_url=request.referrer or url_for("reservations"),
                back_label="Kembali",
                status_code=404
            )


        # ================= UPDATE MENU =================
        if request.method == "POST":

            qty = request.form["qty"]
            menu_id = request.form["menu_id"]
            display_menu_id = request.form.get("display_menu_id")

            fish_type = request.form.get("fish_type")
            fish_size = request.form.get("fish_size")
            fish_weight = request.form.get("fish_weight")
            fish_stock_id = request.form.get("fish_stock_id")
            special_stock_id = request.form.get("special_stock_id")

            special_request = request.form.get("special_request")
            dish_description = request.form.get("dish_description")
            menu_options_json = request.form.get("menu_options_json")
            menu_catalog, _, _ = get_stock_context(cursor, menu["reservation_date"])
            menu_options_json = build_menu_options_payload_from_form(
                request.form,
                menu_catalog,
                display_menu_id,
                fallback_payload=menu_options_json
            )
            resolved_menu_id = resolve_menu_submission(
                menu_catalog,
                menu_id,
                display_menu_id=display_menu_id,
                menu_options_json=menu_options_json
            )
            if resolved_menu_id is None:
                cursor.close()
                conn.close()
                return render_notice_page(
                    "Menu Tidak Valid",
                    "Pilihan menu belum lengkap. Silakan pilih ulang menu yang ingin disimpan.",
                    back_url=url_for("edit_menu", item_id=item_id),
                    back_label="Kembali",
                    status_code=400
                )

            if special_request == "no_special":
                dish_description = None

            if fish_type in ("", "none"):
                fish_type = None

            if fish_size == "":
                fish_size = None

            if fish_weight in ("", "0", "0.0"):
                fish_weight = None

            resolved_fish_stock_id, resolved_special_stock_id = resolve_selected_stock_refs(
                cursor,
                menu["reservation_date"],
                resolved_menu_id,
                fish_type=fish_type,
                fish_weight=fish_weight,
                fish_stock_id=fish_stock_id,
                special_stock_id=special_stock_id
            )

            is_valid_stock, stock_message = validate_stock_request(
                cursor,
                menu["reservation_date"],
                resolved_menu_id,
                qty,
                fish_type=fish_type,
                fish_size=fish_size,
                fish_weight=fish_weight,
                fish_stock_id=resolved_fish_stock_id,
                special_stock_id=resolved_special_stock_id,
                current_item=menu,
                menu_options_json=menu_options_json
            )
            if not is_valid_stock:
                cursor.close()
                conn.close()
                return render_notice_page(
                    "Stock Tidak Cukup",
                    stock_message,
                    back_url=url_for("edit_menu", item_id=item_id),
                    back_label="Kembali",
                    status_code=400
                )

            restore_stock_for_item(cursor, menu)

            cursor.execute("""
                UPDATE reservation_items
                SET quantity=%s,
                    menu_id=%s,
                    fish_type=%s,
                fish_size=%s,
                fish_weight=%s,
                fish_stock_ref_id=%s,
                special_stock_ref_id=%s,
                special_request=%s,
                    dish_description=%s,
                    menu_options_json=%s
                WHERE id=%s
            """,(
                qty,
                resolved_menu_id,
                fish_type,
                fish_size,
                fish_weight,
                resolved_fish_stock_id,
                resolved_special_stock_id,
                special_request,
                dish_description,
                menu_options_json or None,
                item_id
            ))
            previous_menu_label = get_menu_label_for_history(
                cursor,
                menu.get("menu_id"),
                menu_options_json=menu.get("menu_options_json"),
                fallback_name=menu.get("name"),
                fallback_serving_type=menu.get("serving_type")
            )
            updated_menu_label = get_menu_label_for_history(
                cursor,
                resolved_menu_id,
                menu_options_json=menu_options_json
            )
            log_reservation_history(
                cursor,
                menu["reservation_id"],
                "update",
                "menu",
                build_menu_history_summary(
                    "update",
                    updated_menu_label,
                    qty=qty,
                    note=build_menu_display_note(menu_options_json, dish_description),
                    previous_menu_label=previous_menu_label,
                    previous_qty=menu.get("quantity")
                ),
                actor=getattr(current_user, "id", "system"),
                reservation_item_id=item_id
            )

            reduce_stock_after_order(
                cursor,
                fish_stock_id=resolved_fish_stock_id,
                special_stock_id=resolved_special_stock_id,
                qty=int(qty)
            )

            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for("edit_menu", item_id=item_id))


        # ================= CURRENT ORDER =================
        cursor.execute("""
            SELECT
                ri.id,
                ri.quantity,
                ri.special_request,
                ri.dish_description,
                ri.menu_options_json,
                ri.fish_type,
                ri.fish_size,
                ri.fish_weight,
                m.name,
                m.serving_type
            FROM reservation_items ri
            JOIN menus m ON ri.menu_id = m.id
            WHERE ri.reservation_id = %s
            ORDER BY ri.id DESC
            """,(menu["reservation_id"],))

        reservation_menus = cursor.fetchall()
        for item in reservation_menus:
            item["effective_selected_options"] = get_effective_selected_options(item)
            item["display_menu_name"] = format_menu_label(
                get_payload_display_name(
                    item.get("menu_options_json"),
                    item.get("name"),
                    item.get("serving_type")
                ),
                item.get("serving_type")
            )
            item["option_summary"] = build_option_summary_from_row(item)
            item["display_note"] = build_menu_display_note_from_row(item)


        # ================= ALL MENU =================
        all_menus, nila_sizes, sea_fish = get_stock_context(cursor, menu["reservation_date"])
        tuna_stock_menus, tuna_piece_stock, rahang_tuna_stock = get_special_tuna_stock_context(cursor, menu["reservation_date"])

        nila_size_options = [row["size_category"] for row in nila_sizes]

        for fish in sea_fish:
            fish["display_weight"] = format_weight_display(fish["weight_ons"], fish.get("weight_unit"))
            fish["label"] = f"{fish['name'].capitalize()} - {fish['display_weight']} ({fish['fish_count']} stok)"

        menu["special_request_mode"] = "with_special" if menu["dish_description"] else "no_special"

        cursor.close()
        conn.close()

        return render_template(
            "edit_menu.html",
            menu=menu,
            reservation_menus=reservation_menus,
            all_menus=all_menus,
            reservation_id=menu["reservation_id"],
            nila_sizes=nila_size_options,
            sea_fish=sea_fish,
            tuna_piece_stock=tuna_piece_stock,
            rahang_tuna_stock=rahang_tuna_stock,
            selected_date=menu["reservation_date"]
        )


    @app.route("/add_dish/<int:reservation_id>")
    @login_required
    def add_dish_page(reservation_id):

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id,
                customer_name,
                table_number,
                DATE_FORMAT(reservation_datetime, '%Y-%m-%d') AS reservation_date
            FROM reservations
            WHERE id = %s
        """,(reservation_id,))
        reservation = cursor.fetchone()

        if not reservation:
            cursor.close()
            conn.close()
            return render_notice_page(
                "Reservasi Tidak Ditemukan",
                "Data reservasi ini sudah tidak tersedia. Silakan kembali dan pilih reservasi lain.",
                back_url=request.referrer or url_for("reservations"),
                back_label="Kembali",
                status_code=404
            )

        cursor.execute("""
            SELECT
                ri.id,
                ri.quantity,
                ri.special_request,
                ri.dish_description,
                ri.menu_options_json,
                ri.fish_type,
                ri.fish_size,
                ri.fish_weight,
                m.name,
                m.serving_type
            FROM reservation_items ri
            JOIN menus m ON ri.menu_id = m.id
            WHERE ri.reservation_id = %s
            ORDER BY ri.id DESC
        """,(reservation_id,))
        reservation_menus = cursor.fetchall()
        for item in reservation_menus:
            item["effective_selected_options"] = get_effective_selected_options(item)
            item["display_menu_name"] = format_menu_label(
                get_payload_display_name(
                    item.get("menu_options_json"),
                    item.get("name"),
                    item.get("serving_type")
                ),
                item.get("serving_type")
            )
            item["option_summary"] = build_option_summary_from_row(item)
            item["display_note"] = build_menu_display_note_from_row(item)

        all_menus, nila_sizes, sea_fish = get_stock_context(cursor, reservation["reservation_date"])
        _, tuna_piece_stock, rahang_tuna_stock = get_special_tuna_stock_context(cursor, reservation["reservation_date"])

        nila_size_options = [row["size_category"] for row in nila_sizes]
        for fish in sea_fish:
            fish["display_weight"] = format_weight_display(fish["weight_ons"], fish.get("weight_unit"))
            fish["label"] = f"{fish['name'].capitalize()} - {fish['display_weight']} ({fish['fish_count']} stok)"

        cursor.close()
        conn.close()

        return render_template(
            "add_dish.html",
            reservation=reservation,
            reservation_id=reservation_id,
            reservation_menus=reservation_menus,
            all_menus=all_menus,
            nila_sizes=nila_size_options,
            sea_fish=sea_fish,
            tuna_piece_stock=tuna_piece_stock,
            rahang_tuna_stock=rahang_tuna_stock,
            selected_date=reservation["reservation_date"]
        )


    # ================= DELETE MENU =================
    @app.route("/delete_menu/<int:item_id>")
    @login_required
    def delete_menu(item_id):

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        ensure_additional_stock_tables(cursor)

        cursor.execute("""
        SELECT
            ri.id,
            ri.reservation_id,
            ri.quantity,
            ri.fish_type,
            ri.fish_size,
            ri.fish_weight,
            ri.fish_stock_ref_id,
            ri.special_stock_ref_id,
            m.name,
            DATE_FORMAT(r.reservation_datetime, '%Y-%m-%d') AS reservation_date
        FROM reservation_items ri
        JOIN menus m ON m.id = ri.menu_id
        JOIN reservations r ON r.id = ri.reservation_id
        WHERE ri.id = %s
        """,(item_id,))
        item = cursor.fetchone()

        if item:
            restore_stock_for_item(cursor, item)
            log_reservation_history(
                cursor,
                item["reservation_id"],
                "delete",
                "menu",
                f"Menu {item.get('name') or '-'} qty {item.get('quantity') or 0} dihapus.",
                actor=getattr(current_user, "id", "system"),
                reservation_item_id=item_id
            )
            cursor.execute("DELETE FROM reservation_items WHERE id=%s",(item_id,))

        conn.commit()

        cursor.close()
        conn.close()

        fallback_url = url_for("reservation_menu", reservation_id=item["reservation_id"]) if item else url_for("reservations")
        return redirect(request.referrer or fallback_url)

    # ================= ADD MENU =================
    @app.route("/add_menu/<int:reservation_id>", methods=["POST"])
    @login_required
    def add_menu(reservation_id):

        conn = get_db_connection()
        cursor = conn.cursor()
        ensure_additional_stock_tables(cursor)
        reservation_cursor = conn.cursor(dictionary=True)

        menu_id = request.form["menu_id"]
        display_menu_id = request.form.get("display_menu_id")
        qty = request.form["qty"]

        fish_type = request.form.get("fish_type")
        fish_size = request.form.get("fish_size")
        fish_weight = request.form.get("fish_weight")
        fish_stock_id = request.form.get("fish_stock_id")
        special_stock_id = request.form.get("special_stock_id")

        special_request = request.form.get("special_request", "no_special")
        dish_description = request.form.get("dish_description")
        menu_options_json = request.form.get("menu_options_json")

        reservation_cursor.execute("""
        SELECT DATE_FORMAT(reservation_datetime, '%Y-%m-%d') AS reservation_date
        FROM reservations
        WHERE id = %s
        """,(reservation_id,))
        reservation = reservation_cursor.fetchone()
        reservation_date = reservation["reservation_date"] if reservation else None
        menu_catalog, _, _ = get_stock_context(reservation_cursor, reservation_date)
        resolved_menu_id = resolve_menu_submission(
            menu_catalog,
            menu_id,
            display_menu_id=display_menu_id,
            menu_options_json=menu_options_json
        )
        if resolved_menu_id is None:
            conn.rollback()
            reservation_cursor.close()
            cursor.close()
            conn.close()
            return render_notice_page(
                "Menu Tidak Valid",
                "Pilihan menu belum lengkap. Silakan pilih ulang menu yang ingin disimpan.",
                back_url=url_for("add_dish_page", reservation_id=reservation_id),
                back_label="Kembali",
                status_code=400
            )

        if special_request == "no_special":
            dish_description = None

        if fish_type in ("", "none"):
            fish_type = None

        if fish_size == "":
            fish_size = None

        if fish_weight in ("", "0", "0.0"):
            fish_weight = None

        resolved_fish_stock_id, resolved_special_stock_id = resolve_selected_stock_refs(
            reservation_cursor,
            reservation_date,
            resolved_menu_id,
            fish_type=fish_type,
            fish_weight=fish_weight,
            fish_stock_id=fish_stock_id,
            special_stock_id=special_stock_id
        )

        is_valid_stock, stock_message = validate_stock_request(
            reservation_cursor,
            reservation_date,
            resolved_menu_id,
            qty,
            fish_type=fish_type,
            fish_size=fish_size,
            fish_weight=fish_weight,
            fish_stock_id=resolved_fish_stock_id,
            special_stock_id=resolved_special_stock_id,
            menu_options_json=menu_options_json
        )
        if not is_valid_stock:
            conn.rollback()
            reservation_cursor.close()
            cursor.close()
            conn.close()
            return render_notice_page(
                "Stock Tidak Cukup",
                stock_message,
                back_url=url_for("add_dish_page", reservation_id=reservation_id),
                back_label="Kembali",
                status_code=400
            )

        cursor.execute("""
            INSERT INTO reservation_items
            (reservation_id, menu_id, quantity, fish_type, fish_size, fish_weight, fish_stock_ref_id, special_stock_ref_id, special_request, dish_description, menu_options_json)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,(
            reservation_id,
            resolved_menu_id,
            qty,
            fish_type,
            fish_size,
            fish_weight,
            resolved_fish_stock_id,
            resolved_special_stock_id,
            special_request,
            dish_description,
            menu_options_json or None
        ))
        log_reservation_history(
            cursor,
            reservation_id,
            "create",
            "menu",
            build_menu_history_summary(
                "create",
                get_menu_label_for_history(reservation_cursor, resolved_menu_id, menu_options_json=menu_options_json),
                qty=qty,
                note=build_menu_display_note(menu_options_json, dish_description)
            ),
            actor=getattr(current_user, "id", "system"),
            reservation_item_id=cursor.lastrowid
        )

        reduce_stock_after_order(
            cursor,
            fish_stock_id=resolved_fish_stock_id,
            special_stock_id=resolved_special_stock_id,
            qty=int(qty)
        )

        conn.commit()

        reservation_cursor.close()
        cursor.close()
        conn.close()

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return "",204

        return redirect(url_for("add_dish_page", reservation_id=reservation_id))


    @app.route("/reservation_history")
    @login_required
    def reservation_history():
        reservation_id = request.args.get("reservation_id")
        action_type = (request.args.get("action_type") or "").strip().lower()
        allowed_action_types = {"create", "update", "delete"}
        selected_action_type = action_type if action_type in allowed_action_types else None

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        ensure_additional_stock_tables(cursor)

        query = """
                SELECT id, reservation_id, reservation_item_id, action_type, change_scope, summary, actor_name, created_at
                FROM reservation_change_log
        """
        filters = []
        params = []

        if reservation_id and str(reservation_id).isdigit():
            filters.append("reservation_id = %s")
            params.append(reservation_id)

        if selected_action_type:
            filters.append("action_type = %s")
            params.append(selected_action_type)

        if filters:
            query += " WHERE " + " AND ".join(filters)

        query += """
            ORDER BY created_at DESC, id DESC
            LIMIT 300
        """

        cursor.execute(query, tuple(params))

        history_rows = cursor.fetchall()
        history_rows = prepare_reservation_history_rows(cursor, history_rows)
        cursor.close()
        conn.close()

        return render_template(
            "reservation_history.html",
            history_rows=history_rows,
            reservation_id=reservation_id,
            action_type_filter=selected_action_type
        )
