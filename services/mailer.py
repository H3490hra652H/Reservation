import smtplib
from email.message import EmailMessage

from config import get_mail_config


def send_password_reset_email(target_email, username, reset_url, expires_in_minutes):
    mail_config = get_mail_config()

    message = EmailMessage()
    message["Subject"] = "Reset Password Manna Bakery and Cafe"
    message["From"] = f"{mail_config['sender_name']} <{mail_config['username']}>"
    message["To"] = target_email
    message.set_content(
        "\n".join(
            [
                f"Halo {username},",
                "",
                "Kami menerima permintaan reset password untuk akun Manna Bakery and Cafe Anda.",
                "Silakan buka tautan berikut untuk membuat password baru:",
                reset_url,
                "",
                f"Tautan ini berlaku selama {expires_in_minutes} menit dan hanya bisa dipakai satu kali.",
                "Jika Anda tidak meminta reset password, abaikan email ini.",
            ]
        )
    )

    with smtplib.SMTP_SSL(mail_config["host"], mail_config["port"]) as smtp:
        smtp.login(mail_config["username"], mail_config["password"])
        smtp.send_message(message)
