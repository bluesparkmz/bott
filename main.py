"""Bot WhatsApp BlueSpark — FastAPI + webhook.

Deploy na BlueSpark Cloud: liga este repo ao serviço Bot WhatsApp;
push na branch main → redeploy automático.
"""

from __future__ import annotations

import logging
import os
import random
import re
from typing import Any

import requests
from fastapi import FastAPI, Request

logger = logging.getLogger("whatsapp-bot")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="BlueSpark WhatsApp Bot", version="1.0.0")

API_URL = os.getenv(
    "BLUESPARK_WHATSAPP_API_URL",
    "https://cloudmz.bluesparkmz.com/api/whatsapp/dev",
).rstrip("/")
API_KEY = os.getenv("BLUESPARK_WHATSAPP_API_KEY", "").strip()
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook/whatsapp").strip() or "/webhook/whatsapp"
PUBLIC_WEBHOOK = os.getenv("WEBHOOK_PUBLIC_URL", "").strip()

DEV_HINT = (
    "Olá! Bot a funcionar. Se és o dev, personaliza as respostas com IA ou manualmente."
)
RANDOM_WORDS = (
    "ola",
    "sim",
    "ok",
    "blue",
    "spark",
    "moz",
    "bot",
    "ping",
    "hey",
    "vale",
)


def pick_reply(incoming_text: str | None) -> str:
    """Personaliza aqui: IA, regras, menus, etc."""
    _ = incoming_text
    if random.random() < 0.35:
        return random.choice(RANDOM_WORDS)
    return DEV_HINT


def _digits_only(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def _extract_inbound(payload: dict[str, Any]) -> tuple[str | None, str | None]:
    data = payload.get("data")
    if not isinstance(data, dict):
        data = payload
    if isinstance(data, list) and data:
        data = data[0] if isinstance(data[0], dict) else {}

    key = data.get("key") if isinstance(data.get("key"), dict) else {}
    remote = (
        key.get("remoteJid")
        or data.get("remoteJid")
        or data.get("from")
        or payload.get("from")
    )
    number = _digits_only(str(remote or "").split("@")[0])
    if not number:
        return None, None

    message = data.get("message") if isinstance(data.get("message"), dict) else {}
    text = message.get("conversation")
    ext = message.get("extendedTextMessage")
    if not text and isinstance(ext, dict):
        text = ext.get("text")
    if not text and isinstance(message.get("imageMessage"), dict):
        text = message["imageMessage"].get("caption")
    if not text:
        text = data.get("text") or data.get("body")
    if text is not None:
        text = str(text).strip()
    return number or None, text or None


def send_text(number: str, text: str) -> dict[str, Any]:
    if not API_KEY:
        return {"ok": False, "error": "BLUESPARK_WHATSAPP_API_KEY em falta"}
    response = requests.post(
        f"{API_URL}/send-text",
        headers={"X-API-Key": API_KEY},
        json={"number": number, "text": text},
        timeout=30,
    )
    try:
        body = response.json()
    except Exception:
        body = {"raw": response.text[:500]}
    return {"ok": response.ok, "status": response.status_code, "body": body}


def send_media(number: str, mediatype: str, media: str, caption: str = "") -> dict[str, Any]:
    if not API_KEY:
        return {"ok": False, "error": "BLUESPARK_WHATSAPP_API_KEY em falta"}
    payload: dict[str, Any] = {"number": number, "mediatype": mediatype, "media": media}
    if caption:
        payload["caption"] = caption
    response = requests.post(
        f"{API_URL}/send-media",
        headers={"X-API-Key": API_KEY},
        json=payload,
        timeout=60,
    )
    try:
        body = response.json()
    except Exception:
        body = {"raw": response.text[:500]}
    return {"ok": response.ok, "status": response.status_code, "body": body}


@app.get("/")
def root():
    return {
        "service": "BlueSpark WhatsApp Bot",
        "webhook": PUBLIC_WEBHOOK or WEBHOOK_PATH,
        "webhook_hint": "Painel WhatsApp → Webhook = https://teu-subdominio/webhook/whatsapp",
        "api_configured": bool(API_KEY),
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post(WEBHOOK_PATH)
async def whatsapp_webhook(request: Request):
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    event = str(payload.get("event") or payload.get("type") or "").lower()
    number, text = _extract_inbound(payload if isinstance(payload, dict) else {})

    logger.info("webhook event=%s number=%s text=%s", event or "?", number, (text or "")[:80])

    key = {}
    if isinstance(payload, dict):
        data = payload.get("data")
        if isinstance(data, dict):
            key = data.get("key") if isinstance(data.get("key"), dict) else {}
        elif isinstance(data, list) and data and isinstance(data[0], dict):
            key = data[0].get("key") if isinstance(data[0].get("key"), dict) else {}

    if key.get("fromMe") is True:
        return {"ok": True, "ignored": "fromMe"}

    if not number:
        return {"ok": True, "ignored": "no_number"}

    if event and "message" not in event and event not in {"messages.upsert", "messages_upsert"}:
        return {"ok": True, "ignored": event}

    reply = pick_reply(text)
    result = send_text(number, reply)
    return {"ok": True, "replied_to": number, "reply": reply, "send": result}
