from datetime import datetime

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from auth import authenticate_user
from db import get_db_connection
from services.common import (
    effective_stock_status,
    format_weight_display,
    render_notice_page,
    row_value,
    status_indicator,
)
from services.stock import (
    SPECIAL_TUNA_MENU_NAMES,
    get_latest_menu_status_map,
    get_latest_nila_status_map,
    get_latest_sea_fish_stock_rows,
    get_special_tuna_stock_context,
)


def register_auth_main_routes(app):
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form["username"].strip()
            password = request.form["password"]

            user = authenticate_user(username, password)

            if user:
                login_user(user)
                if user.role == "admin":
                    return redirect(url_for("restaurant_landing"))
                return redirect(url_for("home"))

            flash("Login gagal")

        return render_template("login.html")

    @app.errorhandler(404)
    def handle_not_found(error):
        return render_notice_page(
            "Halaman Tidak Ditemukan",
            "Halaman yang Anda cari tidak tersedia atau sudah dipindahkan.",
            status_code=404,
        )

    @app.errorhandler(500)
    def handle_server_error(error):
        return render_notice_page(
            "Terjadi Kesalahan",
            "Sistem sedang mengalami kendala. Silakan kembali ke halaman sebelumnya lalu coba lagi.",
            status_code=500,
        )

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("login"))

    @app.route("/")
    @login_required
    def home():
        selected_date = request.args.get("date")

        if not selected_date:
            selected_date = datetime.now().strftime("%Y-%m-%d")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        _, _, special_tuna_stock = get_special_tuna_stock_context(cursor, selected_date)
        latest_menu_status_map = get_latest_menu_status_map(cursor, selected_date)
        latest_nila_status_map = get_latest_nila_status_map(cursor, selected_date)

        cursor.execute(
            """
        SELECT COUNT(*) AS total_res
        FROM reservations
        WHERE DATE(reservation_datetime)=%s
    """,
            (selected_date,),
        )
        total_res = cursor.fetchone()["total_res"]

        cursor.execute(
            """
        SELECT SUM(people_count) AS total_pax
        FROM reservations
        WHERE DATE(reservation_datetime)=%s
    """,
            (selected_date,),
        )
        total_pax = cursor.fetchone()["total_pax"] or 0

        busy = total_pax > 80

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

        cursor.close()
        conn.close()

        return render_template(
            "home.html",
            total_reservations=total_res,
            total_pax=total_pax,
            busy=busy,
            selected_date=selected_date,
            stock_today=stock_today,
            sea_fish_stock=sea_fish_stock,
            nila_stock=nila_stock,
            special_stock=special_stock,
            rahang_tuna_rows=rahang_tuna_rows,
            rahang_tuna_summary=special_tuna_stock.get("summary", {}),
        )
