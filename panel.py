import os
import httpx

PANEL_BASE_URL = os.getenv("PANEL_BASE_URL", "").rstrip("/")
PANEL_API_KEY = os.getenv("PANEL_API_KEY", "")

async def panel_get_order(order_id: str):
    if not PANEL_BASE_URL or not PANEL_API_KEY:
        return {"error": "Panel not configured"}
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(
            f"{PANEL_BASE_URL}/status",
            data={"key": PANEL_API_KEY, "order": order_id},
        )
        r.raise_for_status()
        return r.json()

async def panel_create_order(service_id: str, quantity: str, link: str):
    if not PANEL_BASE_URL or not PANEL_API_KEY:
        return {"error": "Panel not configured"}
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(
            f"{PANEL_BASE_URL}/add",
            data={
                "key": PANEL_API_KEY,
                "service": service_id,
                "quantity": quantity,
                "link": link,
            },
        )
        r.raise_for_status()
        return r.json()
