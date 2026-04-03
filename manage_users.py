import argparse
import getpass

from auth import set_user_email, upsert_user
from db import init_database


def build_parser():
    parser = argparse.ArgumentParser(description="Kelola user login aplikasi.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_user_parser = subparsers.add_parser("create-user", help="Buat atau update user.")
    create_user_parser.add_argument("username", help="Username login.")
    create_user_parser.add_argument("role", help="Role user, misalnya admin atau kitchen.")
    create_user_parser.add_argument(
        "--full-name",
        help="Nama lengkap user.",
    )
    create_user_parser.add_argument(
        "--email",
        required=True,
        help="Email user untuk login/reset password.",
    )
    create_user_parser.add_argument(
        "--inactive",
        action="store_true",
        help="Simpan user sebagai nonaktif.",
    )

    set_email_parser = subparsers.add_parser("set-email", help="Atur email untuk user yang sudah ada.")
    set_email_parser.add_argument("username", help="Username login.")
    set_email_parser.add_argument("email", help="Email Gmail user.")

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
            email=args.email,
            full_name=args.full_name,
        )
        print(f"User '{args.username}' berhasil disimpan.")
    elif args.command == "set-email":
        updated = set_user_email(args.username.strip(), args.email.strip())
        if not updated:
            raise SystemExit(f"User '{args.username}' tidak ditemukan.")
        print(f"Email untuk user '{args.username}' berhasil diperbarui.")


if __name__ == "__main__":
    main()
