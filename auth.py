from flask_login import LoginManager, UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from db import get_db_connection


login_manager = LoginManager()


class User(UserMixin):
    def __init__(self, db_id, username, role, is_active=True):
        self.db_id = db_id
        self.id = username
        self.username = username
        self.role = role
        self._is_active = bool(is_active)

    @property
    def is_active(self):
        return self._is_active


def _row_to_user(row):
    if not row:
        return None

    return User(
        db_id=row["id"],
        username=row["username"],
        role=row["role"],
        is_active=row["is_active"],
    )


def get_user_by_username(username):
    normalized_username = (username or "").strip()
    if not normalized_username:
        return None

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id, username, password_hash, role, is_active
            FROM app_users
            WHERE username = %s
            LIMIT 1
            """,
            (normalized_username,),
        )
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def authenticate_user(username, password):
    row = get_user_by_username(username)
    if not row or not row["is_active"]:
        return None

    if not check_password_hash(row["password_hash"], password):
        return None

    return _row_to_user(row)


def upsert_user(username, password, role, is_active=True):
    password_hash = generate_password_hash(password)
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO app_users (username, password_hash, role, is_active)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                password_hash = VALUES(password_hash),
                role = VALUES(role),
                is_active = VALUES(is_active),
                updated_at = CURRENT_TIMESTAMP
            """,
            (username, password_hash, role, int(bool(is_active))),
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()


@login_manager.user_loader
def load_user(user_id):
    return _row_to_user(get_user_by_username(user_id))
