
from fastapi import FastAPI, Request
import sqlite3
import asyncio
from crypto import check_invoice

app = FastAPI()
db_lock = asyncio.Lock()

@app.post("/webhook")
async def payment_webhook(req: Request):
    payload = await req.json()
    user_id = await check_invoice(payload)
    if not user_id:
        return {"status": "ignored"}

    async with db_lock:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET subscribed = 1, subscription_expires = datetime('now', '+30 days') WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()

    return {"status": "success"}
