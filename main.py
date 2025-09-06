import os
import json
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, JSONResponse
from dotenv import load_dotenv

from wa import wa_send_text
from panel import panel_get_order, panel_create_order

load_dotenv()
app = FastAPI()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "change_me")

@app.get("/")
async def root():
    return {"ok": True, "service": "whatsapp-bot"}

# -- Webhook Verification (GET) --
@app.get("/webhook/whatsapp")
async def verify_webhook(request: Request):
    p = request.query_params
    if p.get("hub.mode") == "subscribe" and p.get("hub.verify_token") == VERIFY_TOKEN:
        return PlainTextResponse(p.get("hub.challenge", ""), status_code=200)
    return PlainTextResponse("Verification failed", status_code=403)

# -- Incoming Messages (POST) --
@app.post("/webhook/whatsapp")
async def receive_webhook(request: Request):
    body = await request.json()
    print(json.dumps(body, indent=2))  # debug

    try:
        value = body["entry"][0]["changes"][0]["value"]

        # Fast ACK for delivery/read statuses
        if value.get("statuses"):
            return JSONResponse({"status": "ack-status"})

        messages = value.get("messages")
        if not messages:
            return JSONResponse({"status": "ignored"})

        msg = messages[0]
        from_number = msg.get("from")
        text = msg.get("text", {}).get("body", "").strip()

        if not (from_number and text):
            return JSONResponse({"status": "no-text"})

        reply = await handle_command(from_number, text)
        await wa_send_text(from_number, reply)
        return JSONResponse({"status": "sent"})

    except Exception as e:
        print("Webhook error:", e)
        # Still 200 so Meta doesn’t retry forever
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=200)

async def handle_command(sender: str, text: str) -> str:
    parts = text.split()
    cmd = parts[0].lower() if parts else ""

    if cmd in ("hi", "hello", "start"):
        return (
            "👋 Welcome!\n"
            "Commands:\n"
            "• status <order_id>\n"
            "• order <service_id> <qty> <link>\n"
            "• help"
        )

    if cmd == "help":
        return (
            "Usage:\n"
            "• status 12345 → check order status\n"
            "• order 10 100 https://link → create order\n"
        )

    if cmd == "status" and len(parts) >= 2:
        order_id = parts[1]
        data = await panel_get_order(order_id)
        return f"📦 Status for {order_id}:\n{json.dumps(data, indent=2, ensure_ascii=False)}"

    if cmd == "order" and len(parts) >= 4:
        service_id, qty, link = parts[1], parts[2], parts[3]
        data = await panel_create_order(service_id, qty, link)
        return f"🧾 Order result:\n{json.dumps(data, indent=2, ensure_ascii=False)}"

    return "❓ Unknown command. Type *help*."

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
