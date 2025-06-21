
import os
from aiocryptopay import AioCryptoPay, Networks

cryptopay = AioCryptoPay(token=os.getenv("CRYPTOPAY_API_KEY"), network=Networks.MAIN_NET)

async def create_invoice(user_id):
    invoice = await cryptopay.create_invoice(asset="USDT", amount=1.00, hidden_message="Спасибо за покупку!", payload=str(user_id))
    return invoice.bot_invoice_url

async def check_invoice(payload):
    if not payload.get("invoice_id") or payload.get("status") != "paid":
        return None
    return int(payload.get("payload"))
