import argparse
import getpass
import os
import smtplib
from email.message import EmailMessage

DEFAULT_ZIP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "SmartJobPortal.zip")


def send_project_mail(recipient_email, sender_email=None, sender_password=None, smtp_server=None, smtp_port=None):
    if not os.path.exists(DEFAULT_ZIP_PATH):
        print(f"[Error] Project archive not found at: {DEFAULT_ZIP_PATH}")
        return False

    if not sender_email:
        sender_email = input("Enter your email address (sender): ").strip()

    if not sender_password:
        sender_password = getpass.getpass("Enter your email app password / password: ").strip()

    # Auto-detect SMTP server if not specified
    if not smtp_server:
        if "@gmail.com" in sender_email.lower():
            smtp_server = "smtp.gmail.com"
            smtp_port = 465
        elif "@outlook.com" in sender_email.lower() or "@hotmail.com" in sender_email.lower():
            smtp_server = "smtp.office365.com"
            smtp_port = 587
        elif "@yahoo.com" in sender_email.lower():
            smtp_server = "smtp.mail.yahoo.com"
            smtp_port = 465
        else:
            smtp_server = input("Enter your SMTP server (e.g., smtp.gmail.com): ").strip()
            port_input = input("Enter SMTP port (default 465 for SSL, 587 for TLS): ").strip()
            smtp_port = int(port_input) if port_input else 465

    if not smtp_port:
        smtp_port = 465

    msg = EmailMessage()
    msg["Subject"] = "Smart Job Portal - Project Source Code and Documentation"
    msg["From"] = sender_email
    msg["To"] = recipient_email

    body_text = """Hello,

Attached is the complete source code archive for the Smart Job Portal project.

Included in the archive:
- Flask backend application (app.py) with dual database support (MySQL & SQLite fallback)
- Jinja2 templates (dashboard, job listings, registration, login, etc.)
- CSS static assets and uploads directory
- Database schema (database.sql)
- Automated test suite (test_app.py)
- README.md documentation with setup instructions

To run the project:
1. Extract the ZIP file.
2. Install dependencies: pip install -r requirements.txt
3. Start the application: python app.py
4. Open http://127.0.0.1:5000 in your web browser.

Best regards,
Smart Job Portal
"""
    msg.set_content(body_text)

    # Attach the ZIP file
    with open(DEFAULT_ZIP_PATH, "rb") as f:
        file_data = f.read()
        file_name = os.path.basename(DEFAULT_ZIP_PATH)

    msg.add_attachment(file_data, maintype="application", subtype="zip", filename=file_name)

    print(f"Connecting to {smtp_server}:{smtp_port}...")
    try:
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
                server.login(sender_email, sender_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)

        print(f"[Success] Email sent successfully to {recipient_email} with {file_name} attached!")
        return True
    except Exception as e:
        print(f"[Error] Failed to send email: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send Smart Job Portal zip archive via email.")
    parser.add_argument("--to", dest="recipient", help="Recipient email address")
    parser.add_argument("--from", dest="sender", help="Sender email address")
    parser.add_argument("--password", dest="password", help="Sender email password / app password")
    parser.add_argument("--server", dest="server", help="SMTP server host")
    parser.add_argument("--port", dest="port", type=int, help="SMTP server port")

    args = parser.parse_args()

    recipient = args.recipient
    if not recipient:
        recipient = input("Enter recipient email address: ").strip()

    send_project_mail(
        recipient_email=recipient,
        sender_email=args.sender,
        sender_password=args.password,
        smtp_server=args.server,
        smtp_port=args.port
    )
