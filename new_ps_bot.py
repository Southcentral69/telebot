import asyncio
import logging
import aiohttp
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from aiogram.client.default import DefaultBotProperties

# Загрузка .env
load_dotenv()

# Получение токенов
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Проверка токенов
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден! Проверь переменные окружения Railway.")
if not OPENROUTER_API_KEY:
    raise ValueError("❌ OPENROUTER_API_KEY не найден!")

print("✅ Переменные окружения загружены.")
print("BOT_TOKEN начинается с:", BOT_TOKEN[:10])  # Покажи только часть для проверки

# Логирование
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())


# Логирование


# Словарь для хранения языка
user_languages = {}

# Кнопки выбора языка
language_kb = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="Қазақша 🇰🇿", callback_data="lang_kz"),
        InlineKeyboardButton(text="Русский 🇷🇺", callback_data="lang_ru")
    ]
])

@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer("Тілді таңдаңыз / Выберите язык:", reply_markup=language_kb)

@dp.callback_query(F.data.startswith("lang_"))
async def handle_language(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang_code = callback.data.split("_")[1]
    user_languages[user_id] = lang_code

    if lang_code == "kz":
        await callback.message.answer("Сәлем! Мен сенің психолог-досыңмын 🤗 Жасыңды жазып, мазалаған ойыңмен бөліс.")
    else:
        await callback.message.answer("Привет! Я твой психолог 🤗 Напиши свой возраст и расскажи, что у тебя на душе.")

    await callback.answer()

async def ask_openrouter(prompt, age, lang):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://example.com",
        "X-Title": "ChildPsychBot"
    }

    # Системный промпт
    if lang == "kz":
        system_prompt = (
            "Сен — қамқор әрі мейірімді балалар психологысың. "
            f"Сен {age} жастағы баламен қазақ тілінде сөйлесіп тұрсың."
        )
    else:
        system_prompt = (
            "Ты — заботливый и добрый детский психолог. "
            f"Ты общаешься с ребёнком {age} лет."
        )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    json_data = {
        "model": "openai/gpt-4-turbo",
        "messages": messages
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=json_data) as resp:
                data = await resp.json()

                # 👉 Защита от KeyError
                if "choices" not in data:
                    error_msg = data.get("error", {}).get("message", "OpenRouter жауап қайтармады.")
                    return f"⚠️ Қате: {error_msg}"

                return data["choices"][0]["message"]["content"]

    except Exception as e:
        return f"⚠️ Жүйелік қате орын алды: {str(e)}"


@dp.message()
async def handle_message(message: Message):
    user_id = message.from_user.id
    lang = user_languages.get(user_id, "ru")

    text = message.text.strip()
    age = 10
    for word in text.split():
        if word.isdigit() and 3 <= int(word) <= 18:
            age = int(word)
            break

    reply = await ask_openrouter(text, age, lang)
    await message.answer(reply)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
