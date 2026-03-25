from datetime import datetime, timedelta

import mysql.connector
from flask import flash, redirect, render_template, request, url_for

from db import get_db_connection
from services.public_booking import (
    RESTAURANT_PROFILE,
    build_public_booking_description,
    get_restaurant_whatsapp_link,
)


def register_public_routes(app):
    @app.route("/restaurant")
    def restaurant_landing_legacy():
        return redirect(url_for("restaurant_landing"), code=301)

    @app.route("/booking-in-manna")
    def restaurant_landing():
        next_slot = (datetime.now() + timedelta(days=1)).replace(minute=0, second=0, microsecond=0)

        return render_template(
            "restaurant/landing.html",
            restaurant=RESTAURANT_PROFILE,
            whatsapp_link=get_restaurant_whatsapp_link(),
            suggested_datetime=next_slot.strftime("%Y-%m-%dT%H:%M"),
            suggested_min_datetime=datetime.now().strftime("%Y-%m-%dT%H:%M"),
        )

    @app.route("/restaurant/book", methods=["POST"])
    def restaurant_book_legacy():
        return redirect(url_for("restaurant_landing") + "#booking", code=307)

    @app.route("/booking-in-manna/book", methods=["POST"])
    def restaurant_book():
        customer_name = (request.form.get("customer_name") or "").strip()
        whatsapp_number = (request.form.get("whatsapp_number") or "").strip()
        people_count_raw = (request.form.get("people_count") or "").strip()
        reservation_datetime = (request.form.get("reservation_datetime") or "").strip()
        seating_preference = (request.form.get("seating_preference") or "").strip()
        notes = (request.form.get("notes") or "").strip()

        if not customer_name or not whatsapp_number or not people_count_raw or not reservation_datetime:
            flash("Mohon lengkapi nama, WhatsApp, jumlah tamu, dan waktu reservasi.", "error")
            return redirect(url_for("restaurant_landing") + "#booking")

        try:
            people_count = int(people_count_raw)
            if people_count <= 0:
                raise ValueError
        except ValueError:
            flash("Jumlah tamu harus berupa angka lebih dari 0.", "error")
            return redirect(url_for("restaurant_landing") + "#booking")

        try:
            parsed_reservation_datetime = datetime.strptime(reservation_datetime, "%Y-%m-%dT%H:%M")
        except ValueError:
            flash("Format tanggal dan jam reservasi tidak valid.", "error")
            return redirect(url_for("restaurant_landing") + "#booking")

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
            INSERT INTO reservations
            (customer_name, table_number, people_count, reservation_datetime, description)
            VALUES (%s,%s,%s,%s,%s)
        """,
                (
                    customer_name,
                    (seating_preference[:20] if seating_preference else "BOOKING-WEB"),
                    people_count,
                    parsed_reservation_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                    build_public_booking_description(whatsapp_number, seating_preference, notes),
                ),
            )

            reservation_id = cursor.lastrowid
            conn.commit()
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
