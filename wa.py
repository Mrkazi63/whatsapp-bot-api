import os
import httpx

WABA_TOKEN = os.getenv("WABA_TOKEN", "")
WABA_PHONE_ID = os.getenv("WABA_PHONE_ID", "")

async def wa_send_text(to_number: str, text: str):
    """Send a plain text message to a WhatsApp number."""
    url = f"https://graph.facebook.com/v20.0/{WABA_PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {WABA_TOKEN}"}
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
