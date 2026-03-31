import os
from pathlib import Path


_ENV_LOADED = False


def load_env_file():
    global _ENV_LOADED

    if _ENV_LOADED:
        return

    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.exists():
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")

            if key and key not in os.environ:
                os.environ[key] = value

    _ENV_LOADED = True


def get_env(name, default=None, required=False, allow_empty=False):
    load_env_file()
    value = os.getenv(name, default)

    if required and value is None:
        raise RuntimeError(f"Environment variable '{name}' wajib diisi.")

    if required and not allow_empty and str(value).strip() == "":
        raise RuntimeError(f"Environment variable '{name}' wajib diisi.")

    return value


def get_app_secret_key():
    return get_env("APP_SECRET_KEY", required=True)


def get_database_config():
    return {
        "host": get_env("DB_HOST", required=True),
        "user": get_env("DB_USER", required=True),
        "password": get_env("DB_PASSWORD", required=True, allow_empty=True),
        "database": get_env("DB_NAME", required=True),
        "port": int(get_env("DB_PORT", default="3306")),
    }
