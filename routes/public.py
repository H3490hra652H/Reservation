import json
from datetime import datetime, timedelta

import mysql.connector
from flask import flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user

from auth import admin_required, redirect_authenticated_user
from db import get_db_connection
from services.public_booking import (
    RESTAURANT_PROFILE,
    build_booking_resource_sections,
    build_guest_booking_rules,
    build_public_availability_payload,
    build_public_booking_description,
    build_selected_menu_summary,
    ensure_public_booking_tables,
    format_datetime_input,
    get_booking_resource_map,
    get_menu_media_rows,
    get_restaurant_whatsapp_link,
    get_booking_resources,
    is_area_allowed_for_guest_count,
    is_main_table_area,
    normalize_whatsapp_number,
    normalize_booking_area_name,
    parse_booking_items,
    parse_resource_codes_value,
    persist_public_booking_items,
    prepare_public_menu_catalog,
    resolve_booking_end,
    serialize_resource_selection,
)
from services.reservation_floor import ensure_reservation_floor_schema, get_floor_tables


def register_public_routes(app):
    @app.route("/")
    def public_index():
        if current_user.is_authenticated:
            return redirect_authenticated_user()
        return redirect(url_for("restaurant_landing"), code=302)

    @app.route("/restaurant")
    def restaurant_landing_legacy():
        return redirect(url_for("restaurant_landing"), code=301)

    @app.route("/booking-in-manna")
    def restaurant_landing():
        next_slot = (datetime.now() + timedelta(days=1)).replace(minute=0, second=0, microsecond=0)
        default_end = resolve_booking_end(next_slot)
        selected_date = next_slot.strftime("%Y-%m-%d")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            ensure_public_booking_tables(cursor)
            ensure_reservation_floor_schema(cursor)
            menu_catalog, nila_sizes, sea_fish, tuna_piece_stock, rahang_tuna_stock = prepare_public_menu_catalog(cursor, selected_date)
            resource_sections = build_booking_resource_sections(cursor, next_slot, default_end)
            floor_tables = get_floor_tables(cursor)
        finally:
            cursor.close()
            conn.close()

        booking_bootstrap_json = json.dumps(
            {
                "menu_catalog": menu_catalog,
                "nila_sizes": nila_sizes,
                "sea_fish": sea_fish,
                "tuna_piece_stock": tuna_piece_stock,
                "rahang_tuna_stock": rahang_tuna_stock,
                "availability": resource_sections,
                "floor_tables": floor_tables,
                "guest_rules": build_guest_booking_rules(),
            },
            ensure_ascii=False,
            default=str,
        )

        return render_template(
            "restaurant/landing.html",
            restaurant=RESTAURANT_PROFILE,
            whatsapp_link=get_restaurant_whatsapp_link(),
            suggested_datetime=format_datetime_input(next_slot),
            suggested_end_datetime=format_datetime_input(default_end),
            suggested_min_datetime=format_datetime_input(datetime.now()),
            booking_bootstrap_json=booking_bootstrap_json,
        )

    @app.route("/restaurant/book", methods=["POST"])
    def restaurant_book_legacy():
        return redirect(url_for("restaurant_landing") + "#booking", code=307)

    @app.route("/booking-in-manna/availability")
    def restaurant_booking_availability():
        start_value = (request.args.get("start") or "").strip()
        end_value = (request.args.get("end") or "").strip()

        try:
            start_datetime = datetime.strptime(start_value, "%Y-%m-%dT%H:%M")
            end_datetime = datetime.strptime(end_value, "%Y-%m-%dT%H:%M")
        except ValueError:
            return jsonify({"error": "Format waktu tidak valid."}), 400

        if end_datetime <= start_datetime:
            return jsonify({"error": "Waktu selesai harus lebih besar dari waktu mulai."}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            ensure_public_booking_tables(cursor)
            payload = build_public_availability_payload(cursor, start_datetime, end_datetime)
        finally:
            cursor.close()
            conn.close()

        return jsonify(payload)

    @app.route("/booking-in-manna/book", methods=["POST"])
    def restaurant_book():
        customer_name = (request.form.get("customer_name") or "").strip()
        whatsapp_number = normalize_whatsapp_number(request.form.get("whatsapp_number"))
        people_count_raw = (request.form.get("people_count") or "").strip()
        reservation_datetime = (request.form.get("reservation_datetime") or "").strip()
        booking_end_datetime = (request.form.get("booking_end_datetime") or "").strip()
        booking_area = normalize_booking_area_name(request.form.get("booking_area"))
        booking_resource_code = (request.form.get("booking_resource_code") or "").strip()
        booking_resource_codes_raw = request.form.get("booking_resource_codes") or ""
        booking_extra_chairs_raw = (request.form.get("booking_extra_chairs") or "").strip()
        notes = (request.form.get("notes") or "").strip()
        booking_items_payload = request.form.get("booking_items_payload") or "[]"

        if not customer_name or not whatsapp_number or not people_count_raw or not reservation_datetime or not booking_end_datetime:
            flash("Mohon lengkapi nama, WhatsApp, jumlah tamu, jam mulai, dan jam selesai booking.", "error")
            return redirect(url_for("restaurant_landing") + "#booking")

        if not booking_area or not (booking_resource_codes_raw or booking_resource_code):
            flash("Silakan pilih area booking dan meja atau setup ruang yang tersedia.", "error")
            return redirect(url_for("restaurant_landing") + "#booking")

        try:
            people_count = int(people_count_raw)
            if people_count <= 0:
                raise ValueError
        except ValueError:
            flash("Jumlah tamu harus berupa angka lebih dari 0.", "error")
            return redirect(url_for("restaurant_landing") + "#booking")

        try:
            booking_extra_chairs = int(booking_extra_chairs_raw or 0)
            if booking_extra_chairs < 0:
                raise ValueError
        except ValueError:
            flash("Tambahan kursi harus berupa angka 0 atau lebih.", "error")
            return redirect(url_for("restaurant_landing") + "#booking")

        try:
            parsed_reservation_datetime = datetime.strptime(reservation_datetime, "%Y-%m-%dT%H:%M")
            parsed_booking_end_datetime = datetime.strptime(booking_end_datetime, "%Y-%m-%dT%H:%M")
        except ValueError:
            flash("Format tanggal dan jam booking tidak valid.", "error")
            return redirect(url_for("restaurant_landing") + "#booking")

        if parsed_booking_end_datetime <= parsed_reservation_datetime:
            flash("Jam selesai booking harus lebih besar dari jam mulai.", "error")
            return redirect(url_for("restaurant_landing") + "#booking")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            ensure_public_booking_tables(cursor)
            resource_map = get_booking_resource_map(cursor)
            selected_codes = parse_resource_codes_value(booking_resource_codes_raw) or parse_resource_codes_value(booking_resource_code)
            selected_resources = [resource_map.get(code) for code in selected_codes]
            if not selected_codes or any(not resource or not int(resource.get("is_active") or 0) for resource in selected_resources):
                raise ValueError("Pilihan area booking sudah tidak tersedia.")
            resolved_area = normalize_booking_area_name(selected_resources[0].get("area_name"))
            if any(normalize_booking_area_name(resource.get("area_name")) != resolved_area for resource in selected_resources):
                raise ValueError("Semua pilihan meja harus berasal dari area booking yang sama.")
            if resolved_area != booking_area:
                booking_area = resolved_area
            if not is_area_allowed_for_guest_count(resolved_area, people_count):
                raise ValueError(
                    f"Untuk jumlah tamu lebih dari {VIP_MAX_GUESTS} orang, area yang dapat dipilih hanya Hall, Outdoor, atau Ruang Utama."
                )
            if not is_main_table_area(resolved_area) and len(selected_resources) > 1:
                raise ValueError("Selain Ruang Utama, pilihan tempat hanya boleh satu area atau satu setup.")
            if not is_main_table_area(resolved_area) and booking_extra_chairs > 0:
                raise ValueError("Tambahan kursi hanya tersedia untuk pilihan Ruang Utama.")

            total_capacity = sum(int(resource.get("seat_capacity") or 0) for resource in selected_resources)
            if is_main_table_area(resolved_area):
                total_capacity += booking_extra_chairs
            if total_capacity > 0 and total_capacity < people_count:
                raise ValueError("Total kursi dari meja yang dipilih belum cukup untuk jumlah tamu. Silakan tambah meja atau kursi tambahan.")

            selected_date = parsed_reservation_datetime.strftime("%Y-%m-%d")
            menu_catalog, _, _, _, _ = prepare_public_menu_catalog(cursor, selected_date)

            booked_codes = set(
                build_public_availability_payload(
                    cursor,
                    parsed_reservation_datetime,
                    parsed_booking_end_datetime,
                )["booked_codes"]
            )
            conflicting_codes = [code for code in selected_codes if code in booked_codes]
            if conflicting_codes:
                raise ValueError("Meja atau setup ruang yang Anda pilih sudah dibooking di jam tersebut.")

            parsed_items = parse_booking_items(booking_items_payload)
            selected_menu_summary = build_selected_menu_summary(parsed_items, menu_catalog)
            primary_resource = selected_resources[0]
            serialized_table_label = serialize_resource_selection(selected_resources, extra_chairs=booking_extra_chairs)
            booking_setup_value = None if is_main_table_area(resolved_area) else primary_resource.get("setup_key")
            booking_notes = notes
            if booking_extra_chairs > 0:
                booking_notes = f"{booking_notes} | Tambahan kursi: {booking_extra_chairs}" if booking_notes else f"Tambahan kursi: {booking_extra_chairs}"

            cursor.execute(
                """
                INSERT INTO reservations (
                    customer_name, whatsapp_number, table_number, people_count,
                    reservation_datetime, booking_end_datetime, description,
                    booking_source, booking_area, booking_resource_code, booking_resource_codes, booking_setup
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    customer_name,
                    whatsapp_number,
                    serialized_table_label,
                    people_count,
                    parsed_reservation_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                    parsed_booking_end_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                    build_public_booking_description(
                        whatsapp_number,
                        serialized_table_label,
                        booking_notes,
                        selected_menus=selected_menu_summary,
                    ),
                    "public_web",
                    booking_area,
                    primary_resource.get("resource_code"),
                    json.dumps(selected_codes, ensure_ascii=False),
                    booking_setup_value,
                ),
            )
            reservation_id = cursor.lastrowid

            persist_public_booking_items(cursor, reservation_id, selected_date, booking_items_payload)
            conn.commit()
        except ValueError as error:
            conn.rollback()
            flash(str(error), "error")
            return redirect(url_for("restaurant_landing") + "#booking")
        except mysql.connector.Error:
            conn.rollback()
            flash("Booking belum bisa diproses. Silakan coba lagi beberapa saat.", "error")
            return redirect(url_for("restaurant_landing") + "#booking")
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for("restaurant_booking_success", reservation_id=reservation_id))

    @app.route("/restaurant/booking-success/<int:reservation_id>")
    def restaurant_booking_success_legacy(reservation_id):
        return redirect(url_for("restaurant_booking_success", reservation_id=reservation_id), code=301)

    @app.route("/booking-in-manna/booking-success/<int:reservation_id>")
    def restaurant_booking_success(reservation_id):
        return render_template(
            "restaurant/booking_success.html",
            restaurant=RESTAURANT_PROFILE,
            reservation_id=reservation_id,
            whatsapp_link=get_restaurant_whatsapp_link(
                f"Halo Manna Bakery and Cafe, saya ingin konfirmasi booking dengan kode #{reservation_id}."
            ),
        )

    @app.route("/booking_settings")
    @admin_required
    def booking_settings():
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            ensure_public_booking_tables(cursor)
            booking_resources = get_booking_resources(cursor)
            menu_media_rows = get_menu_media_rows(cursor)
        finally:
            cursor.close()
            conn.close()

        return render_template(
            "booking_settings.html",
            booking_resources=booking_resources,
            menu_media_rows=menu_media_rows,
        )

    @app.route("/booking_settings/resources", methods=["POST"])
    @admin_required
    def save_booking_resources():
        resource_ids = request.form.getlist("resource_id[]")
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            ensure_public_booking_tables(cursor)
            for resource_id in resource_ids:
                if not str(resource_id).isdigit():
                    continue
                cursor.execute(
                    """
                    UPDATE booking_resources
                    SET area_name=%s,
                        display_name=%s,
                        table_label=%s,
                        seat_capacity=%s,
                        image_url=%s,
                        description=%s,
                        is_active=%s,
                        sort_order=%s
                    WHERE id=%s
                    """,
                    (
                        request.form.get(f"area_name_{resource_id}", ""),
                        request.form.get(f"display_name_{resource_id}", ""),
                        request.form.get(f"table_label_{resource_id}", "") or None,
                        int(request.form.get(f"seat_capacity_{resource_id}") or 0),
                        request.form.get(f"image_url_{resource_id}", "") or None,
                        request.form.get(f"description_{resource_id}", "") or None,
                        int(request.form.get(f"is_active_{resource_id}") or 0),
                        int(request.form.get(f"sort_order_{resource_id}") or 0),
                        int(resource_id),
                    ),
                )
            conn.commit()
            flash("Pengaturan area booking berhasil diperbarui.", "success")
        except mysql.connector.Error:
            conn.rollback()
            flash("Pengaturan area booking gagal disimpan.", "error")
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for("booking_settings"))

    @app.route("/booking_settings/menu-media", methods=["POST"])
    @admin_required
    def save_booking_menu_media():
        menu_ids = request.form.getlist("menu_id[]")
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            ensure_public_booking_tables(cursor)
            for menu_id in menu_ids:
                if not str(menu_id).isdigit():
                    continue
                image_url = (request.form.get(f"image_url_{menu_id}") or "").strip()
                short_description = (request.form.get(f"short_description_{menu_id}") or "").strip()
                cursor.execute(
                    """
                    INSERT INTO menu_display_assets (menu_id, image_url, short_description)
                    VALUES (%s,%s,%s)
                    ON DUPLICATE KEY UPDATE
                        image_url = VALUES(image_url),
                        short_description = VALUES(short_description)
                    """,
                    (int(menu_id), image_url or None, short_description or None),
                )
            conn.commit()
            flash("Foto dan deskripsi menu booking berhasil disimpan.", "success")
        except mysql.connector.Error:
            conn.rollback()
            flash("Foto menu booking gagal disimpan.", "error")
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for("booking_settings"))
