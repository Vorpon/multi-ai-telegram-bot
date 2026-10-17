import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from config import TELEGRAM_BOT_TOKEN, OPENROUTER_API_KEY
from route import route_request
from image_generator import generate_image
from vision_analyzer import analyze_image_with_prompt
from openai import OpenAI
from aiocryptopay import AioCryptoPay, Networks
from aiocryptopay.models.invoice import Invoice
from dotenv import load_dotenv
from keep_alive import keep_alive

# Функция создания главного меню
def get_main_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Выбрать ИИ-модель", callback_data="choose_ai")],
        [InlineKeyboardButton(text="💎 Пополнить баланс (CryptoBot)", callback_data="top_up")],
        [InlineKeyboardButton(text="🛠 Техподдержка", url="https://t.me/твой_логин_поддержки")] # Ссылка на чат с поддержкой
    ])
    return keyboard

load_dotenv()
CRYPTO_PAY_TOKEN = os.getenv("CRYPTO_PAY_TOKEN")

# Инициализация CryptoBot
crypto = None

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# Простейшее хранилище премиум-пользователей
premium_users = set()

# Фоновая задача для поддержания статуса «печатает...»
async def send_typing_action(bot_inst, chat_id):
    try:
        while True:
            await bot_inst.send_chat_action(chat_id=chat_id, action="typing")
            await asyncio.sleep(4)
    except asyncio.CancelledError:
        pass

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🤖 **Привет! Я твой мультимодальный AI-агрегатор.**\n\n"
        "Ты можешь:\n"
        "• Писать мне тексты и задавать вопросы\n"
        "• Просить создать концепт картинки (например: *«Нарисуй кота в космосе»*)\n"
        "• Присылать фотографии с текстом для анализа!",
        parse_mode="Markdown"
    )

@dp.message(F.text)
async def handle_text(message: types.Message):
    user_text = message.text
    user_id = message.from_user.id
    request_type = route_request(user_text)
    
    if request_type == "image":
        if user_id not in premium_users:
            pay_url = "https://t.me/CryptoBot"
            if crypto:
                try:
                    invoice: Invoice = await crypto.create_invoice(
                        amount=600.0,
                        currency_type="fiat",
                        fiat="RUB",
                        accepted_assets="USDT,TON",
                        description="Премиум-подписка AI-агрегатора на 30 дней",
                        payload=str(user_id)
                    )
                    pay_url = invoice.pay_url
                except Exception as e:
                    logging.error(f"Ошибка создания счета CryptoBot: {e}")

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="💳 Оплатить подписку (600 ₽)", url=pay_url)],
                    [InlineKeyboardButton(text="🔄 Проверить оплату", callback_data="check_payment")]
                ]
            )
            
            await message.answer(
                "🔒 **Требуется Премиум-доступ**\n\n"
                "Генерация визуальных концептов доступна в рамках премиум-подписки. "
                "Оплатите доступ удобным способом через CryptoBot, чтобы разблокировать функцию!",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            return

        # Запускаем непрерывную анимацию печати
        typing_task = asyncio.create_task(send_typing_action(bot, message.chat.id))
        try:
            # Выполняем генерацию картинки в фоновом потоке, не замораживая интерфейс
            result = await asyncio.to_thread(generate_image, user_text)
            typing_task.cancel()
            await message.answer(result)
        except Exception as e:
            typing_task.cancel()
            await message.answer(f"❌ Произошла ошибка: {e}")
    else:
        # Запускаем непрерывную анимацию «печатает...» для текста
        typing_task = asyncio.create_task(send_typing_action(bot, message.chat.id))
        try:
            # Выполняем запрос к OpenAI/DeepSeek в фоновом потоке через to_thread
            def get_completion():
                return client.chat.completions.create(
                    model="deepseek/deepseek-chat",
                    messages=[{"role": "user", "content": user_text}],
                    max_tokens=1500
                )

            completion = await asyncio.to_thread(get_completion)
            answer_text = completion.choices[0].message.content
            
            typing_task.cancel()
            
            # Возвращаем Markdown разметку — заголовки и списки станут красивыми
            await message.answer(answer_text, parse_mode="Markdown")
            
        except Exception as e:
            typing_task.cancel()
            await message.answer(f"❌ Произошла ошибка при обращении к модели: {e}")


# Обработчик кнопки "Выбрать ИИ-модель"
@dp.callback_query(F.data == "choose_ai")
async def process_choose_ai(callback: CallbackQuery):
    ai_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧠 GPT-4o", callback_data="set_ai_gpt4")],
        [InlineKeyboardButton(text="⚡ Claude 3.5 Sonnet", callback_data="set_ai_claude")],
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_menu")]
    ])
    await callback.message.edit_text("Выбери нейросеть, с которой хочешь общаться:", reply_markup=ai_keyboard)
    await callback.answer()

# Обработчик возврата в главное меню
@dp.callback_query(F.data == "back_to_menu")
async def process_back_menu(callback: CallbackQuery):
    await callback.message.edit_text("Главное меню:", reply_markup=get_main_menu())
    await callback.answer()
@dp.callback_query(F.data == "top_up")
async def process_top_up(callback: CallbackQuery):
    user_id = callback.from_user.id
    if not crypto:
        await callback.message.answer("⚠️ Платежная система временно недоступна.")
        await callback.answer()
        return

    try:
        # Создаем инвойс через CryptoBot (например, на 5 USDT или любая другая сумма)
        invoice = await crypto.create_invoice(
            asset="USDT", 
            amount=5.0, 
            payload=str(user_id),
            description="Пополнение баланса / Премиум-доступ"
        )
        
        # Клавиатура с кнопкой оплаты и кнопкой проверки
        pay_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить в CryptoBot", url=invoice.pay_url)],
            [InlineKeyboardButton(text="🔄 Проверить оплату", callback_data="check_payment")],
            [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_menu")]
        ])
        
        await callback.message.edit_text(
            "💎 **Пополнение баланса**\n\n"
            "Нажмите кнопку ниже для оплаты счета через CryptoBot. После успешной оплаты нажмите «Проверить оплату».",
            reply_markup=pay_keyboard,
            parse_mode="Markdown"
        )
    except Exception as e:
        await callback.message.answer(f"Ошибка создания счета: {e}")
    
    await callback.answer()
    
@dp.callback_query(F.data == "check_payment")
async def check_payment_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if crypto:
        try:
            invoices = await crypto.get_invoices(status="paid")
            is_paid = any(str(inv.payload) == str(user_id) for inv in invoices)
            
            if is_paid or user_id in premium_users:
                premium_users.add(user_id)
                await callback.message.answer("🎉 Оплата найдена! Премиум-доступ успешно активирован. Можете отправлять запрос на генерацию.")
            else:
                await callback.answer("⏳ Оплата пока не поступила. Попробуйте чуть позже после завершения платежа.", show_alert=True)
                return
        except Exception as e:
            await callback.answer(f"Ошибка проверки: {e}", show_alert=True)
            return
    await callback.answer()

@dp.message(F.photo)
async def handle_photo(message: types.Message):
    typing_task = asyncio.create_task(send_typing_action(bot, message.chat.id))
    try:
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        downloaded_file_path = f"temp_{photo.file_id}.jpg"
        await bot.download(file_info.file_path, destination=downloaded_file_path)
        
        caption = message.caption if message.caption else "Опиши подробно, что на этой картинке."
        analysis_result = await asyncio.to_thread(analyze_image_with_prompt, downloaded_file_path, caption)
        
        if os.path.exists(downloaded_file_path):
            os.remove(downloaded_file_path)
            
        typing_task.cancel()
        await message.answer(analysis_result, parse_mode="Markdown")
    except Exception as e:
        typing_task.cancel()
        await message.answer(f"❌ Ошибка при анализе фото: {e}")

async def main():
    
    keep_alive()
    # Запускаем фоновый HTTP-сервер для Render
    global crypto
    if CRYPTO_PAY_TOKEN:
        crypto = AioCryptoPay(token=CRYPTO_PAY_TOKEN)

    print("🚀 Telegram-бот запущен и работает стабильно!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())