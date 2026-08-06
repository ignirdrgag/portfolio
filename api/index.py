import json
import os
import re
import smtplib
from email.message import EmailMessage
from http.server import BaseHTTPRequestHandler

OWNER_EMAIL = os.getenv("OWNER_EMAIL", "abessolofreddy2005@gmail.com")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]{2,}$")

MAX_NAME = 100
MAX_EMAIL = 200
MAX_SUBJECT = 150
MAX_MESSAGE = 5000


def _send_email(name, email, subject, message):
    msg = EmailMessage()
    sender = SMTP_USER if SMTP_USER else OWNER_EMAIL
    msg["From"] = f"{name} <{sender}>"
    msg["To"] = OWNER_EMAIL
    msg["Reply-To"] = email
    msg["Subject"] = f"[Portfolio] {subject}"
    msg.set_content(
        "Nouveau message depuis le portfolio\n"
        "--------------------------------\n"
        f"Nom : {name}\n"
        f"Email : {email}\n"
        f"Sujet : {subject}\n\n"
        f"Message :\n{message}\n"
    )
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)


class handler(BaseHTTPRequestHandler):

    server_version = "PortfolioAPI"

    def _send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._send_json(405, {"ok": False, "error": "Méthode non autorisée."})

    def do_POST(self):
        if not SMTP_USER or not SMTP_PASSWORD:
            return self._send_json(500, {"ok": False, "error": "SMTP non configuré côté serveur."})

        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        try:
            data = json.loads(raw.decode("utf-8")) if raw else {}
        except Exception:
            data = {}
        if not isinstance(data, dict):
            data = {}

        name = str(data.get("name", "")).strip()[:MAX_NAME]
        email = str(data.get("email", "")).strip()[:MAX_EMAIL]
        subject = str(data.get("subject", "")).strip()[:MAX_SUBJECT]
        message = str(data.get("message", "")).strip()[:MAX_MESSAGE]

        errors = {}
        if len(name) < 2:
            errors["name"] = "Nom invalide."
        if not EMAIL_RE.match(email):
            errors["email"] = "Email invalide."
        if not subject:
            errors["subject"] = "Sujet requis."
        if len(message) < 10:
            errors["message"] = "Message trop court (10 caractères min.)."

        if errors:
            return self._send_json(422, {"ok": False, "errors": errors})

        try:
            _send_email(name, email, subject, message)
        except Exception:
            return self._send_json(500, {"ok": False, "error": "Envoi impossible. Réessayez plus tard."})

        return self._send_json(200, {"ok": True, "message": "Message envoyé."})

    def log_message(self, format, *args):
        pass
