import html as html_mod
import json
import mimetypes
import os
import re
import smtplib
from email.message import EmailMessage
from http.server import BaseHTTPRequestHandler

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

OWNER_EMAIL = os.getenv("OWNER_EMAIL", "abessolofreddy2005@gmail.com")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

SITE_URL = os.getenv("SITE_URL", "https://portfolio-e59o.vercel.app")

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]{2,}$")

MAX_NAME = 100
MAX_EMAIL = 200
MAX_SUBJECT = 150
MAX_MESSAGE = 5000


def _render_html_email(name, email, subject, message):
    e_name = html_mod.escape(name)
    e_email = html_mod.escape(email)
    e_subject = html_mod.escape(subject)
    e_message = html_mod.escape(message).replace("\n", "<br>")
    return (
        '<!DOCTYPE html><html><body style="margin:0;padding:0;background:#f0fdf4;font-family:Arial,Helvetica,sans-serif;">'
        '<div style="max-width:600px;margin:0 auto;padding:32px 16px;">'
        '<div style="background:#ffffff;border-radius:14px;overflow:hidden;border:1px solid #bbf7d0;">'
        f'<table cellpadding="0" cellspacing="0" border="0" style="width:100%;background:linear-gradient(135deg,#16a34a,#15803d);">'
        f'<tr><td style="padding:22px 0 22px 28px;vertical-align:middle;">'
        f'<img src="{SITE_URL}/icons/ja.svg" alt="" width="48" height="48" style="border-radius:10px;display:block;">'
        f'</td>'
        f'<td style="padding:22px 28px 22px 14px;vertical-align:middle;">'
        f'<div style="font-size:19px;font-weight:800;color:#ffffff;">Nouveau message</div>'
        f'<div style="font-size:13px;color:#dcfce7;margin-top:3px;">Formulaire de contact — portfolio</div>'
        f'</td></tr></table>'
        '<div style="padding:28px;">'
        f'<table cellpadding="0" cellspacing="0" border="0" style="width:100%;font-size:14px;color:#14532d;">'
        f'<tr><td style="padding:7px 0;color:#15803d;width:96px;vertical-align:top;font-weight:700;">Nom</td>'
        f'<td style="padding:7px 0;font-weight:600;color:#14532d;">{e_name}</td></tr>'
        f'<tr><td style="padding:7px 0;color:#15803d;width:96px;vertical-align:top;font-weight:700;">Email</td>'
        f'<td style="padding:7px 0;"><a href="mailto:{e_email}" style="color:#15803d;text-decoration:none;font-weight:600;">{e_email}</a></td></tr>'
        f'<tr><td style="padding:7px 0;color:#15803d;width:96px;vertical-align:top;font-weight:700;">Sujet</td>'
        f'<td style="padding:7px 0;font-weight:600;color:#14532d;">{e_subject}</td></tr>'
        '</table>'
        f'<div style="margin-top:16px;padding:16px 18px;background:#f0fdf4;border-left:3px solid #16a34a;border-radius:8px;font-size:14px;color:#166534;line-height:1.6;">{e_message}</div>'
        '</div>'
        f'<div style="background:#f0fdf4;padding:14px 28px;border-top:1px solid #bbf7d0;font-size:12px;color:#166534;">'
        f'Abessolo Ovono Jean Freddy — Développeur Backend Django · <a href="{SITE_URL}" style="color:#15803d;text-decoration:none;">portfolio-e59o.vercel.app</a>'
        '</div>'
        '</div>'
        '</div>'
        '</body></html>'
    )


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
    msg.add_alternative(_render_html_email(name, email, subject, message), subtype="html")
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)


class handler(BaseHTTPRequestHandler):

    server_version = "Portfolio"

    def _send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_static(self, raw_path):
        path = (raw_path or "/").split("?", 1)[0].split("#", 1)[0]
        if path in ("", "/"):
            path = "/index.html"
        rel = path.lstrip("/")
        if not rel or ".." in rel or "\x00" in rel:
            return self._send_json(404, {"ok": False, "error": "Introuvable."})
        filepath = os.path.join(BASE_DIR, rel)
        if not os.path.isfile(filepath):
            return self._send_json(404, {"ok": False, "error": "Introuvable."})
        try:
            with open(filepath, "rb") as f:
                body = f.read()
        except Exception:
            return self._send_json(500, {"ok": False, "error": "Erreur de lecture."})
        ctype, _ = mimetypes.guess_type(filepath)
        self.send_response(200)
        self.send_header("Content-Type", ctype or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._serve_static(self.path)

    def do_HEAD(self):
        self.do_GET()

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
