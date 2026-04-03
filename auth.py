import hashlib
import secrets
from datetime import datetime, timedelta
from functools import wraps

import mysql.connector
from flask import flash, redirect, request, url_for
from flask_login import LoginManager, UserMixin, current_user
from werkzeug.security import check_password_hash, generate_password_hash

from config import get_password_reset_token_minutes
from db import get_db_connection


login_manager = LoginManager()
PASSWORD_MIN_LENGTH = 8
VALID_ROLES = {"user", "kitchen", "admin"}
ROLE_HOME_ENDPOINTS = {
    "user": "user_dashboard",
    "kitchen": "stock_overview",
    "admin": "home",
}


class User(UserMixin):
    def __init__(self, db_id, username, full_name, role, is_active=True, email=None):
        self.id = str(db_id)
        self.db_id = db_id
        self.username = username
        self.full_name = full_name or username
        self.role = role
        self.email = email
        self._is_active = bool(is_active)

    @property
    def is_active(self):
        return self._is_active

    @property
    def display_name(self):
        return self.full_name or self.username


def normalize_email(email):
    return (email or "").strip().lower()


def normalize_username(username):
    return (username or "").strip()


def normalize_role(role):
    normalized_role = (role or "").strip().lower()
    if normalized_role not in VALID_ROLES:
        raise ValueError("Role tidak valid.")
    return normalized_role


def validate_password(password):
    normalized_password = (password or "").strip()
    if len(normalized_password) < PASSWORD_MIN_LENGTH:
        raise ValueError(f"Password minimal {PASSWORD_MIN_LENGTH} karakter.")
    return normalized_password


def _row_to_user(row):
    if not row:
        return None

    return User(
        db_id=row["id"],
        username=row["username"],
        full_name=row.get("full_name"),
        role=row["role"],
        is_active=row["is_active"],
        email=row.get("email"),
    )


def get_role_home_endpoint(role):
    return ROLE_HOME_ENDPOINTS.get((role or "").strip().lower(), "login")


def get_authenticated_home_url():
    if not current_user.is_authenticated:
        return url_for("login")
    return url_for(get_role_home_endpoint(getattr(current_user, "role", None)))


def redirect_authenticated_user():
    return redirect(get_authenticated_home_url())


@login_manager.unauthorized_handler
def handle_unauthorized():
    flash("Silakan login dulu untuk melanjutkan.", "error")
    next_url = request.path if request.method == "GET" else None
    if next_url:
        return redirect(url_for("login", next=next_url))
    return redirect(url_for("login"))


def role_required(*roles):
    allowed_roles = {normalize_role(role) for role in roles}

    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            if not current_user.is_authenticated:
                return login_manager.unauthorized()

            if getattr(current_user, "role", None) not in allowed_roles:
                flash("Akses ditolak untuk halaman tersebut.", "error")
                return redirect(get_authenticated_home_url())

            if not getattr(current_user, "is_active", False):
                flash("Akun Anda sedang nonaktif. Hubungi admin.", "error")
                return redirect(url_for("logout"))

            return view_func(*args, **kwargs)

        return wrapped_view

    return decorator


def admin_required(view_func):
    return role_required("admin")(view_func)


def _is_duplicate_entry_error(error):
    return isinstance(error, mysql.connector.Error) and getattr(error, "errno", None) == 1062


def _hash_reset_token(token):
    return hashlib.sha256((token or "").encode("utf-8")).hexdigest()


def _base_user_select_sql():
    return """
        SELECT id, username, full_name, email, password_hash, role, is_active, created_at, updated_at
        FROM users
    """


def get_user_by_id(user_id):
    if user_id in (None, ""):
        return None

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(_base_user_select_sql() + " WHERE id = %s LIMIT 1", (user_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def get_user_by_username(username):
    normalized_username = normalize_username(username)
    if not normalized_username:
        return None

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(_base_user_select_sql() + " WHERE username = %s LIMIT 1", (normalized_username,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def get_user_by_email(email):
    normalized_email = normalize_email(email)
    if not normalized_email:
        return None

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(_base_user_select_sql() + " WHERE email = %s LIMIT 1", (normalized_email,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def authenticate_user(identity, password):
    normalized_identity = (identity or "").strip()
    if not normalized_identity or not password:
        return None

    user_row = get_user_by_email(normalized_identity) if "@" in normalized_identity else get_user_by_username(normalized_identity)
    if not user_row or not user_row["is_active"]:
        return None

    if not check_password_hash(user_row["password_hash"], password):
        return None

    return _row_to_user(user_row)


def count_admin_users(exclude_user_id=None):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        query = "SELECT COUNT(*) FROM users WHERE role = 'admin' AND is_active = 1"
        params = []
        if exclude_user_id is not None:
            query += " AND id <> %s"
            params.append(exclude_user_id)
        cursor.execute(query, tuple(params))
        row = cursor.fetchone()
        return int(row[0] if row else 0)
    finally:
        cursor.close()
        conn.close()


def create_user(username, password, email, role="user", full_name=None, is_active=True):
    normalized_username = normalize_username(username)
    normalized_email = normalize_email(email)
    normalized_role = normalize_role(role)
    normalized_password = validate_password(password)
    normalized_full_name = (full_name or "").strip() or normalized_username

    if not normalized_username:
        raise ValueError("Username wajib diisi.")
    if not normalized_email:
        raise ValueError("Email wajib diisi.")

    password_hash = generate_password_hash(normalized_password)
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO users (username, full_name, email, password_hash, role, is_active)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (normalized_username, normalized_full_name, normalized_email, password_hash, normalized_role, int(bool(is_active))),
        )
        conn.commit()
        return cursor.lastrowid
    except mysql.connector.Error as error:
        conn.rollback()
        if _is_duplicate_entry_error(error):
            raise ValueError("Username atau email sudah digunakan.") from error
        raise
    finally:
        cursor.close()
        conn.close()


def upsert_user(username, password, role, is_active=True, email=None, full_name=None):
    existing_user = get_user_by_username(username)
    if existing_user:
        update_user_by_admin(
            existing_user["id"],
            username=username,
            email=email or existing_user.get("email"),
            full_name=full_name or existing_user.get("full_name"),
            role=role,
            is_active=is_active,
            new_password=password,
        )
        return existing_user["id"]

    return create_user(
        username=username,
        password=password,
        email=email,
        role=role,
        full_name=full_name,
        is_active=is_active,
    )


def set_user_email(username, email):
    existing_user = get_user_by_username(username)
    if not existing_user:
        return False

    update_user_profile(existing_user["id"], existing_user.get("full_name"), email)
    return True


def list_users():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            _base_user_select_sql()
            + """
            ORDER BY
                CASE role
                    WHEN 'admin' THEN 1
                    WHEN 'kitchen' THEN 2
                    ELSE 3
                END,
                username ASC
            """
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def update_user_profile(user_id, full_name, email):
    normalized_full_name = (full_name or "").strip()
    normalized_email = normalize_email(email)
    if not normalized_full_name:
        raise ValueError("Nama lengkap wajib diisi.")
    if not normalized_email:
        raise ValueError("Email wajib diisi.")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            UPDATE users
            SET full_name = %s,
                email = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (normalized_full_name, normalized_email, user_id),
        )
        conn.commit()
    except mysql.connector.Error as error:
        conn.rollback()
        if _is_duplicate_entry_error(error):
            raise ValueError("Email sudah digunakan.") from error
        raise
    finally:
        cursor.close()
        conn.close()


def change_user_password(user_id, current_password, new_password):
    user_row = get_user_by_id(user_id)
    if not user_row:
        raise ValueError("User tidak ditemukan.")
    if not check_password_hash(user_row["password_hash"], current_password or ""):
        raise ValueError("Password saat ini tidak benar.")

    new_password = validate_password(new_password)
    new_password_hash = generate_password_hash(new_password)

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            UPDATE users
            SET password_hash = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (new_password_hash, user_id),
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def update_user_by_admin(user_id, username, email, full_name, role, is_active=True, new_password=None):
    normalized_username = normalize_username(username)
    normalized_email = normalize_email(email)
    normalized_full_name = (full_name or "").strip() or normalized_username
    normalized_role = normalize_role(role)

    if not normalized_username:
        raise ValueError("Username wajib diisi.")
    if not normalized_email:
        raise ValueError("Email wajib diisi.")

    existing_user = get_user_by_id(user_id)
    if not existing_user:
        raise ValueError("User tidak ditemukan.")

    if existing_user["role"] == "admin":
        if normalized_role != "admin" and count_admin_users(exclude_user_id=user_id) == 0:
            raise ValueError("Harus ada minimal satu admin aktif.")
        if not bool(is_active) and count_admin_users(exclude_user_id=user_id) == 0:
            raise ValueError("Admin terakhir tidak boleh dinonaktifkan.")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        if new_password:
            normalized_password = validate_password(new_password)
            password_hash = generate_password_hash(normalized_password)
            cursor.execute(
                """
                UPDATE users
                SET username = %s,
                    full_name = %s,
                    email = %s,
                    role = %s,
                    is_active = %s,
                    password_hash = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (
                    normalized_username,
                    normalized_full_name,
                    normalized_email,
                    normalized_role,
                    int(bool(is_active)),
                    password_hash,
                    user_id,
                ),
            )
        else:
            cursor.execute(
                """
                UPDATE users
                SET username = %s,
                    full_name = %s,
                    email = %s,
                    role = %s,
                    is_active = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (
                    normalized_username,
                    normalized_full_name,
                    normalized_email,
                    normalized_role,
                    int(bool(is_active)),
                    user_id,
                ),
            )
        conn.commit()
    except mysql.connector.Error as error:
        conn.rollback()
        if _is_duplicate_entry_error(error):
            raise ValueError("Username atau email sudah digunakan.") from error
        raise
    finally:
        cursor.close()
        conn.close()


def create_password_reset_token(email):
    user_row = get_user_by_email(email)
    if not user_row or not user_row["is_active"]:
        return None

    plain_token = secrets.token_urlsafe(32)
    token_hash = _hash_reset_token(plain_token)
    expires_at = datetime.now() + timedelta(minutes=get_password_reset_token_minutes())

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            UPDATE reset_tokens
            SET used_at = CURRENT_TIMESTAMP
            WHERE user_id = %s
              AND used_at IS NULL
            """,
            (user_row["id"],),
        )
        cursor.execute(
            """
            INSERT INTO reset_tokens (user_id, token_hash, expires_at)
            VALUES (%s, %s, %s)
            """,
            (user_row["id"], token_hash, expires_at),
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()

    return {
        "token": plain_token,
        "email": user_row["email"],
        "username": user_row["username"],
        "expires_in_minutes": get_password_reset_token_minutes(),
    }


def reset_password_with_token(token, new_password):
    normalized_token = (token or "").strip()
    if not normalized_token:
        return False

    password_hash = generate_password_hash(validate_password(new_password))
    token_hash = _hash_reset_token(normalized_token)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT rt.id, rt.user_id, rt.expires_at, u.is_active
            FROM reset_tokens rt
            JOIN users u ON u.id = rt.user_id
            WHERE rt.token_hash = %s
              AND rt.used_at IS NULL
            LIMIT 1
            """,
            (token_hash,),
        )
        token_row = cursor.fetchone()
        if not token_row:
            return False
        if not token_row["is_active"]:
            return False
        if token_row["expires_at"] is None or token_row["expires_at"] < datetime.now():
            return False

        cursor.execute(
            """
            UPDATE users
            SET password_hash = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (password_hash, token_row["user_id"]),
        )
        cursor.execute(
            """
            UPDATE reset_tokens
            SET used_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (token_row["id"],),
        )
        conn.commit()
        return True
    finally:
        cursor.close()
        conn.close()


@login_manager.user_loader
def load_user(user_id):
    return _row_to_user(get_user_by_id(user_id))
