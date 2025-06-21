
import logging
import sqlite3
import asyncio
import sys
import os
from datetime import datetime
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, BotCommand, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.session.aiohttp import AiohttpSession
from openai import OpenAI
from crypto import create_invoice

# === Загрузка переменных окружения ===
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ADMIN_ID = os.getenv("ADMIN_ID", "1082828397")
FREE_USES_LIMIT = 10

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не задан в .env")
if not OPENAI_API_KEY:
    raise ValueError("❌ OPENAI_API_KEY не задан в .env")

# === Инициализация клиентов ===
client = OpenAI(api_key=OPENAI_API_KEY)
session = AiohttpSession()
bot = Bot(token=BOT_TOKEN, session=session)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# === Настройка БД ===
logging.basicConfig(level=logging.INFO)
conn = sqlite3.connect("users.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    usage_count INTEGER DEFAULT 0,
    subscribed INTEGER DEFAULT 0,
    subscription_expires TEXT,
    joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
    notified_renewal INTEGER DEFAULT 0
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS history (
    user_id INTEGER,
    type TEXT,
    prompt TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

# === FSM Состояния ===
class GenStates(StatesGroup):
    await_text = State()
    await_image = State()

class StateAssistant(StatesGroup):
    dialog = State()

user_histories = {}

def is_subscribed(user_id):
    cursor.execute("SELECT subscribed FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    return row and row[0] == 1

def ensure_user(user_id):
    cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()

def get_usage_count(user_id):
    cursor.execute("SELECT usage_count FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    return row[0] if row else 0

def get_stats():
    cursor.execute("SELECT COUNT(*), SUM(subscribed) FROM users")
    total, subs = cursor.fetchone()
    return f"📊 Пользователей: {total}\n🟢 Подписчиков: {subs or 0}"

def main_menu():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="✍️ Сгенерировать текст"), KeyboardButton(text="🖼 Создать изображение")],
        [KeyboardButton(text="🧠 Умный помощник")],
        [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="💰 Купить подписку")],
        [KeyboardButton(text="📚 Как пользоваться?"), KeyboardButton(text="⚙️ Настройки модели")],
        [KeyboardButton(text="📊 Админка")],
    ], resize_keyboard=True)

# === Хендлеры ===
@dp.message(Command("start"))
async def start_handler(message: Message):
    ensure_user(message.from_user.id)
    await message.answer("📢 Добро пожаловать! Выберите действие:", reply_markup=main_menu())

@dp.message(F.text == "💰 Купить подписку")
async def menu_buy(message: Message):
    url = await create_invoice(message.from_user.id)
    btn = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Оплатить $1", url=url)]])
    await message.answer("💳 После оплаты подписка активируется автоматически.", reply_markup=btn)

# Остальные хендлеры будут добавлены позже

async def main():
    await bot.set_my_commands([
        BotCommand(command="start", description="Запуск бота"),
        BotCommand(command="buy", description="Купить подписку")
    ])
    await dp.start_polling(bot)

if __name__ == "__main__":
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
