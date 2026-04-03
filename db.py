import mysql.connector
from werkzeug.security import generate_password_hash

from config import get_database_config, get_default_admin_config


USERS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INT NOT NULL AUTO_INCREMENT,
    username VARCHAR(100) NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(255) NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('user', 'kitchen', 'admin') NOT NULL DEFAULT 'user',
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_users_username (username),
    UNIQUE KEY uq_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
"""

RESET_TOKENS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS reset_tokens (
    id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    token_hash CHAR(64) NOT NULL,
    expires_at DATETIME NOT NULL,
    used_at DATETIME NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_reset_tokens_token_hash (token_hash),
    KEY idx_reset_tokens_user_id (user_id),
    KEY idx_reset_tokens_expires_at (expires_at),
    CONSTRAINT fk_reset_tokens_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
"""


def get_db_connection():
    return mysql.connector.connect(**get_database_config())


def _column_exists(cursor, table_name, column_name):
    cursor.execute(
        """
        SELECT 1
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND COLUMN_NAME = %s
        LIMIT 1
        """,
        (table_name, column_name),
    )
    return cursor.fetchone() is not None


def _table_exists(cursor, table_name):
    cursor.execute(
        """
        SELECT 1
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
        LIMIT 1
        """,
        (table_name,),
    )
    return cursor.fetchone() is not None


def _migrate_legacy_users(cursor):
    if not _table_exists(cursor, "app_users"):
        return

    cursor.execute(
        """
        INSERT INTO users (username, full_name, email, password_hash, role, is_active, created_at, updated_at)
        SELECT
            au.username,
            COALESCE(NULLIF(TRIM(au.username), ''), 'User Legacy'),
            au.email,
            au.password_hash,
            CASE
                WHEN au.role IN ('user', 'kitchen', 'admin') THEN au.role
                ELSE 'user'
            END,
            au.is_active,
            au.created_at,
            au.updated_at
        FROM app_users au
        LEFT JOIN users u ON u.username = au.username
        WHERE u.id IS NULL
        """
    )


def _ensure_default_admin(cursor):
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
    row = cursor.fetchone()
    if row and int(row[0]) > 0:
        return

    admin_config = get_default_admin_config()
    cursor.execute(
        """
        INSERT INTO users (username, full_name, email, password_hash, role, is_active)
        VALUES (%s, %s, %s, %s, 'admin', 1)
        """,
        (
            admin_config["username"].strip(),
            admin_config["full_name"].strip() or admin_config["username"].strip(),
            admin_config["email"].strip().lower(),
            generate_password_hash(admin_config["password"]),
        ),
    )


def init_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(USERS_TABLE_SQL)
        cursor.execute(RESET_TOKENS_TABLE_SQL)

        if not _column_exists(cursor, "users", "full_name"):
            cursor.execute("ALTER TABLE users ADD COLUMN full_name VARCHAR(150) NOT NULL DEFAULT 'User' AFTER username")

        _migrate_legacy_users(cursor)
        _ensure_default_admin(cursor)
        try:
            from services.public_booking import ensure_public_booking_tables

            ensure_public_booking_tables(cursor)
        except Exception:
            pass
        conn.commit()
    finally:
        cursor.close()
        conn.close()
