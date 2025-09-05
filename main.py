import os
import json
from typing import Any, Dict, Optional

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, JSONResponse
from dotenv import load_dotenv

from wa import wa_send_text
from panel import panel_get_order, panel_create_order

load_dotenv()
app = FastAPI()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "change_me")

# ====== Health ======
@app.get("/")
async def root():
    return {"ok": True, "service": "whatsapp-bot"}

# ====== Webhook verification (GET) ======
@app.get("/webhook/whatsapp")
async def verify_webhook(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return PlainTextResponse(content=challenge or "", status_code=200)
    return PlainTextResponse(content="Verification failed", status_code=403)

# ====== Receive messages (POST) ======
@app.post("/webhook/whatsapp")
async def receive_webhook(request: Request):
    body = await request.json()
    # Log everything for debugging
    print(json.dumps(body, indent=2))

    try:
        entry = body["entry"][0]
        change = entry["changes"][0]
        value = change["value"]

        # messages array exists when a new incoming message arrives
        messages = value.get("messages")
        if not messages:
            return JSONResponse({"status": "ignored"})

        msg = messages[0]
        from_number = msg.get("from")            # WhatsApp number as string (E.164 without +)
        text = None

        # text message
        if msg.get("type") == "text":
            text = msg["text"]["body"].strip()

        if not (from_number and text):
            return JSONResponse({"status": "no-text"})

        # Basic command router
        reply = await handle_command(from_number, text)
        await wa_send_text(from_number, reply)

        return JSONResponse({"status": "sent"})

    except Exception as e:
        print("Webhook error:", e)
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=200)

# ====== Command handlers ======
async def handle_command(sender: str, text: str) -> str:
    parts = text.split()
    cmd = parts[0].lower()

    if cmd in ("hi", "hello", "start"):
        return (
            "👋 Welcome! Commands:\n"
            "• status <order_id>\n"
            "• order <service_id> <qty> <link>\n"
            "• help"
        )

    if cmd == "help":
        return (
            "Help:\n"
            "status 12345 → check order status\n"
            "order 10 100 https://link → create order\n"
        )

    if cmd == "status" and len(parts) >= 2:
        order_id = parts[1]
        data = await panel_get_order(order_id)
        return f"📦 Status for {order_id}:\n{json.dumps(data, indent=2)}"

    if cmd == "order" and len(parts) >= 4:
        service_id, qty, link = parts[1], parts[2], parts[3]
        data = await panel_create_order(service_id, qty, link)
        return f"🧾 Order result:\n{json.dumps(data, indent=2)}"

    return "❓ Unknown command. Type *help*."

# ====== Run (for local/dev use) ======
# In production you'll run with: `uvicorn main:app --host 0.0.0.0 --port 8000`
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
