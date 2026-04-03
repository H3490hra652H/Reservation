import sys
from datetime import datetime
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user

from auth import (
    admin_required,
    authenticate_user,
    create_password_reset_token,
    create_user,
    get_authenticated_home_url,
    normalize_email,
    redirect_authenticated_user,
    reset_password_with_token,
    validate_password,
)
from config import get_password_reset_allowed_email
from db import get_db_connection
from services.common import (
    effective_stock_status,
    format_weight_display,
    render_notice_page,
    row_value,
    status_indicator,
)
from services.mailer import send_password_reset_email
from services.stock import (
    SPECIAL_TUNA_MENU_NAMES,
    get_latest_menu_status_map,
    get_latest_nila_status_map,
    get_latest_sea_fish_stock_rows,
    get_special_tuna_stock_context,
)


def register_auth_main_routes(app):
    allowed_reset_email = get_password_reset_allowed_email()

    def resolve_password_reset_email():
        submitted_email = normalize_email(request.form.get("email") or request.args.get("email"))
        if allowed_reset_email:
            return allowed_reset_email
        return submitted_email

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect_authenticated_user()

        if request.method == "GET" and request.args.get("logged_out") == "1":
            flash("Anda sudah logout.", "success")

        if request.method == "POST":
            identity = (request.form.get("username") or "").strip()
            password = request.form.get("password") or ""
            user = authenticate_user(identity, password)

            if user:
                login_user(user)
                flash(f"Selamat datang, {user.display_name}.", "success")
                next_page = (request.args.get("next") or "").strip()
                if next_page.startswith("/"):
                    return redirect(next_page)
                return redirect(get_authenticated_home_url())

            flash("Login gagal. Periksa username/email dan password Anda.", "error")

        if request.method == "GET":
            return render_template("login.html")

        return render_template("login.html", identity=(request.form.get("username") or "").strip())

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if current_user.is_authenticated:
            return redirect_authenticated_user()

        if request.method == "POST":
            full_name = (request.form.get("full_name") or "").strip()
            username = (request.form.get("username") or "").strip()
            email = normalize_email(request.form.get("email"))
            password = request.form.get("password") or ""
            confirm_password = request.form.get("confirm_password") or ""

            try:
                if not full_name or not username or not email or not password or not confirm_password:
                    raise ValueError("Lengkapi nama, username, email, dan password.")
                if password != confirm_password:
                    raise ValueError("Konfirmasi password tidak cocok.")

                validate_password(password)
                create_user(
                    username=username,
                    password=password,
                    email=email,
                    role="user",
                    full_name=full_name,
                    is_active=True,
                )
                flash("Registrasi berhasil. Silakan login dengan akun baru Anda.", "success")
                return redirect(url_for("login"))
            except ValueError as error:
                flash(str(error), "error")

        return render_template("register.html")

    @app.route("/forgot-password", methods=["GET", "POST"])
    def forgot_password():
        email = resolve_password_reset_email()

        if request.method == "POST":
            if not email:
                flash("Masukkan email yang terdaftar dulu.", "error")
                return render_template(
                    "forgot_password.html",
                    email=email,
                    password_reset_locked=bool(allowed_reset_email),
                )

            try:
                reset_payload = create_password_reset_token(email)
                if reset_payload:
                    reset_url = url_for("reset_password", token=reset_payload["token"], _external=True)
                    send_password_reset_email(
                        target_email=reset_payload["email"],
                        username=reset_payload["username"],
                        reset_url=reset_url,
                        expires_in_minutes=reset_payload["expires_in_minutes"],
                    )
                flash("Jika email terdaftar, tautan reset password sudah dikirim.", "success")
                return redirect(url_for("login"))
            except RuntimeError:
                flash("Fitur kirim email belum dikonfigurasi. Isi MAIL_USERNAME dan MAIL_PASSWORD di file .env.", "error")
            except Exception:
                flash("Tautan reset password gagal dikirim. Silakan coba lagi.", "error")

        return render_template(
            "forgot_password.html",
            email=email,
            password_reset_locked=bool(allowed_reset_email),
        )

    @app.route("/reset-password", methods=["GET", "POST"])
    def reset_password():
        token = (request.form.get("token") or request.args.get("token") or "").strip()

        if request.method == "POST":
            new_password = request.form.get("new_password") or ""
            confirm_password = request.form.get("confirm_password") or ""

            try:
                if not token or not new_password or not confirm_password:
                    raise ValueError("Tautan reset atau password baru belum lengkap.")
                if new_password != confirm_password:
                    raise ValueError("Konfirmasi password tidak cocok.")
                validate_password(new_password)
                if not reset_password_with_token(token, new_password):
                    raise ValueError("Token reset tidak valid, sudah digunakan, atau sudah kedaluwarsa.")
                flash("Password berhasil diubah. Silakan login dengan password baru Anda.", "success")
                return redirect(url_for("login"))
            except ValueError as error:
                flash(str(error), "error")

        return render_template("reset_password.html", token=token)

    @app.route("/logout")
    def logout():
        logout_user()
        return redirect(url_for("login", logged_out=1))

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

    @app.route("/home")
    @admin_required
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

    @app.route("/app")
    def app_home():
        return redirect_authenticated_user()


if __name__ == "__main__":
    from app import create_app

    create_app().run(debug=True)
