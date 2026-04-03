from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user

from auth import (
    admin_required,
    change_user_password,
    create_user,
    list_users,
    role_required,
    update_user_by_admin,
    update_user_profile,
)


def register_account_routes(app):
    @app.route("/dashboard/user")
    @role_required("user")
    def user_dashboard():
        return render_template("user_dashboard.html")

    @app.route("/profile", methods=["GET", "POST"])
    @role_required("user", "kitchen", "admin")
    def profile():
        if request.method == "POST":
            action = (request.form.get("action") or "").strip()

            try:
                if action == "profile":
                    update_user_profile(
                        current_user.db_id,
                        request.form.get("full_name"),
                        request.form.get("email"),
                    )
                    flash("Profile berhasil diperbarui.", "success")
                elif action == "password":
                    current_password = request.form.get("current_password") or ""
                    new_password = request.form.get("new_password") or ""
                    confirm_password = request.form.get("confirm_password") or ""
                    if new_password != confirm_password:
                        raise ValueError("Konfirmasi password baru tidak cocok.")
                    change_user_password(current_user.db_id, current_password, new_password)
                    flash("Password berhasil diubah.", "success")
                else:
                    flash("Aksi tidak dikenali.", "error")
            except ValueError as error:
                flash(str(error), "error")

            return redirect(url_for("profile"))

        return render_template("profile.html")

    @app.route("/admin")
    @admin_required
    def admin_index():
        return redirect(url_for("admin_users"))

    @app.route("/admin/users", methods=["GET", "POST"])
    @admin_required
    def admin_users():
        if request.method == "POST":
            try:
                password = request.form.get("password") or ""
                confirm_password = request.form.get("confirm_password") or ""
                if password != confirm_password:
                    raise ValueError("Konfirmasi password user baru tidak cocok.")

                create_user(
                    username=request.form.get("username"),
                    password=password,
                    email=request.form.get("email"),
                    role=request.form.get("role"),
                    full_name=request.form.get("full_name"),
                    is_active=request.form.get("is_active") == "1",
                )
                flash("User baru berhasil dibuat.", "success")
                return redirect(url_for("admin_users"))
            except ValueError as error:
                flash(str(error), "error")

        return render_template("admin_users.html", users=list_users())

    @app.route("/admin/users/<int:user_id>/update", methods=["POST"])
    @admin_required
    def admin_update_user(user_id):
        try:
            new_password = (request.form.get("new_password") or "").strip() or None
            update_user_by_admin(
                user_id=user_id,
                username=request.form.get("username"),
                email=request.form.get("email"),
                full_name=request.form.get("full_name"),
                role=request.form.get("role"),
                is_active=request.form.get("is_active") == "1",
                new_password=new_password,
            )
            flash("Data user berhasil diperbarui.", "success")
        except ValueError as error:
            flash(str(error), "error")

        return redirect(url_for("admin_users"))
