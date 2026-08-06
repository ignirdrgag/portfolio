import html as html_mod
import os
import re
import smtplib
import threading
import time
from email.message import EmailMessage

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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

RATE_LIMIT = 5
RATE_WINDOW = 3600
_rate = {}
_lock = threading.Lock()

app = Flask(__name__)
CORS(app)


def _rate_limited(ip):
    now = time.time()
    with _lock:
        recent = [t for t in _rate.get(ip, []) if now - t < RATE_WINDOW]
        _rate[ip] = recent
        if len(recent) >= RATE_LIMIT:
            return True
        recent.append(now)
        return False


def _render_html_email(name, email, subject, message):
    e_name = html_mod.escape(name)
    e_email = html_mod.escape(email)
    e_subject = html_mod.escape(subject)
    e_message = html_mod.escape(message).replace("\n", "<br>")
    return (
        '<!DOCTYPE html><html><body style="margin:0;padding:0;background:#f6f8fb;font-family:Inter,Arial,sans-serif;">'
        '<div style="max-width:600px;margin:0 auto;padding:32px 16px;">'
        '<div style="background:#ffffff;border-radius:14px;overflow:hidden;border:1px solid #e2e8f0;">'
        '<div style="background:linear-gradient(135deg,#0f766e,#115e59);padding:24px 28px;">'
        '<div style="font-size:20px;font-weight:800;color:#ffffff;">Nouveau message</div>'
        '<div style="font-size:13px;color:#e6f2f1;margin-top:4px;">Formulaire de contact — portfolio</div>'
        '</div>'
        '<div style="padding:28px;">'
        f'<table cellpadding="0" cellspacing="0" border="0" style="width:100%;font-size:14px;color:#334155;">'
        f'<tr><td style="padding:6px 0;color:#5b6b7f;width:96px;vertical-align:top;">Nom</td>'
        f'<td style="padding:6px 0;font-weight:600;color:#0f172a;">{e_name}</td></tr>'
        f'<tr><td style="padding:6px 0;color:#5b6b7f;width:96px;vertical-align:top;">Email</td>'
        f'<td style="padding:6px 0;"><a href="mailto:{e_email}" style="color:#0f766e;text-decoration:none;font-weight:600;">{e_email}</a></td></tr>'
        f'<tr><td style="padding:6px 0;color:#5b6b7f;width:96px;vertical-align:top;">Sujet</td>'
        f'<td style="padding:6px 0;font-weight:600;color:#0f172a;">{e_subject}</td></tr>'
        '</table>'
        f'<div style="margin-top:16px;padding:16px 18px;background:#f0f4f9;border-left:3px solid #0f766e;border-radius:8px;font-size:14px;color:#334155;line-height:1.6;">{e_message}</div>'
        '</div>'
        '<div style="background:#f0f4f9;padding:14px 28px;border-top:1px solid #e2e8f0;font-size:12px;color:#5b6b7f;">'
        'Abessolo Ovono Jean Freddy — Développeur Backend Django · '
        '<a href="https://portfolio-e59o.vercel.app" style="color:#0f766e;text-decoration:none;">portfolio-e59o.vercel.app</a>'
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


@app.get("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.get("/<path:filename>")
def static_files(filename):
    return send_from_directory(BASE_DIR, filename)


@app.post("/api/contact")
def contact():
    if not SMTP_USER or not SMTP_PASSWORD:
        return jsonify({"ok": False, "error": "SMTP non configuré côté serveur."}), 500

    if _rate_limited(request.remote_addr or "unknown"):
        return jsonify({"ok": False, "error": "Trop de messages. Réessayez plus tard."}), 429

    data = request.get_json(silent=True) or {}
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
        return jsonify({"ok": False, "errors": errors}), 422

    try:
        _send_email(name, email, subject, message)
    except Exception:
        return jsonify({"ok": False, "error": "Envoi impossible. Réessayez plus tard."}), 500

    return jsonify({"ok": True, "message": "Message envoyé."}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
