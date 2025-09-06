# wa.py
import os
import httpx
from dotenv import load_dotenv

load_dotenv()  # <-- make sure .env is loaded

WABA_TOKEN = os.getenv("WABA_TOKEN", "").strip()       # strip is IMPORTANT
WABA_PHONE_ID = os.getenv("WABA_PHONE_ID", "").strip()

GRAPH_BASE = "https://graph.facebook.com"
GRAPH_VERSION = "v20.0"

async def wa_send_text(to_number: str, text: str):
    if not (WABA_TOKEN and WABA_PHONE_ID):
        raise RuntimeError("WABA_TOKEN/WABA_PHONE_ID missing in environment")

    url = f"{GRAPH_BASE}/{GRAPH_VERSION}/{WABA_PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WABA_TOKEN}",   # now safe
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": text},
    }

    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        return r.json()
