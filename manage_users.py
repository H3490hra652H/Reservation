import argparse
import getpass

from auth import upsert_user
from db import init_database


def build_parser():
    parser = argparse.ArgumentParser(description="Kelola user login aplikasi.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_user_parser = subparsers.add_parser("create-user", help="Buat atau update user.")
    create_user_parser.add_argument("username", help="Username login.")
    create_user_parser.add_argument("role", help="Role user, misalnya admin atau kitchen.")
    create_user_parser.add_argument(
        "--inactive",
        action="store_true",
        help="Simpan user sebagai nonaktif.",
    )

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    init_database()

    if args.command == "create-user":
        password = getpass.getpass("Password user: ").strip()
        password_confirmation = getpass.getpass("Ulangi password: ").strip()

        if not password:
            raise SystemExit("Password tidak boleh kosong.")

        if password != password_confirmation:
            raise SystemExit("Konfirmasi password tidak cocok.")

        upsert_user(
            username=args.username.strip(),
            password=password,
            role=args.role.strip(),
            is_active=not args.inactive,
        )
        print(f"User '{args.username}' berhasil disimpan.")


if __name__ == "__main__":
    main()
