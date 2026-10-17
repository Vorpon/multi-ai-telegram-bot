import os
from dotenv import load_dotenv

# Загружаем переменные из файла .env
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not OPENROUTER_API_KEY:
    raise ValueError("❌ Ошибка: Не найден OPENROUTER_API_KEY в переменных окружения!")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("❌ Ошибка: Не найден TELEGRAM_BOT_TOKEN в переменных окружения!")