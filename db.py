import mysql.connector

from config import get_database_config


AUTH_USERS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS app_users (
    id INT NOT NULL AUTO_INCREMENT,
    username VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_app_users_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
"""


def get_db_connection():
    return mysql.connector.connect(**get_database_config())


def init_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(AUTH_USERS_TABLE_SQL)
        conn.commit()
    finally:
        cursor.close()
        conn.close()
