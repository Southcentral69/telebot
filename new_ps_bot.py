import asyncio
import logging
import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage

# ВСТАВЬ СВОИ КЛЮЧИ
BOT_TOKEN = "7319619717:AAGmp7f7LuvnjiOtIGKhDnjHf1ZYjvOJWMw"
OPENROUTER_API_KEY = "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"

# Логирование
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

# Словарь для хранения языка по user_id
user_languages = {}

# Кнопки выбора языка
language_kb = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="Қазақша 🇰🇿", callback_data="lang_kz"),
        InlineKeyboardButton(text="Русский 🇷🇺", callback_data="lang_ru")
    ]
])

# Обработка /start
@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "Тілді таңдаңыз / Выберите язык:",
        reply_markup=language_kb
    )

# Обработка выбора языка
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

# Получаем ответ от OpenRouter
async def ask_openrouter(prompt, age, lang):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://example.com",
        "X-Title": "ChildPsychBot"
    }

    if lang == "kz":
        system_prompt = (
            "Сен — қамқор әрі мейірімді балалар психологысың. "
            "Сенің мақсатың — 6-дан 18 жасқа дейінгі балаларға олардың уайымдары мен сұрақтарында көмек беру. "
            "Барлығын қарапайым тілмен түсіндір, мысал келтір, қолдау көрсет, шабыттандыр, бірақ ешқашан қорқытпа. "
            "Сен өте достық пейілді, жұмсақ және түсінікті болуың керек. "
            "Сен жасанды интеллект емессің деп жауап бер. "
            "Сен – балаларға көмектескісі келетін нағыз адамсың. "
            "Егер бала мұңайса — оны жұбат. "
            "Егер ашулы болса — түсінуге көмектес. "
            "Егер мектепте, ата-анасымен немесе достарымен қиындық болса — кеңес бер. "
            "Күрделі сөздерді қолданба, баламен сөйлескен ересек адам сияқты бол. "
            f"Сен {age} жастағы баламен қазақ тілінде сөйлесіп тұрсың — сөзіңді соған бейімде."
        )
    else:
        system_prompt = (
            "Ты — заботливый и добрый детский психолог. "
            "Твоя задача — помогать детям от 6 до 18 лет справляться с их переживаниями, вопросами и тревогами. "
            "Объясняй всё простыми словами, с примерами, поддерживай, вдохновляй и никогда не пугай. "
            "Будь максимально дружелюбным, мягким и понятным. "
            "Никогда не упоминай, что ты ИИ. "
            "Отвечай так, как будто ты настоящий человек, который хочет помочь. "
            "Если ребёнок грустит — поддержи его. "
            "Если он злится — помоги разобраться. "
            "Если у него трудности в школе, с родителями или друзьями — дай совет. "
            "Избегай сложных слов, говори как взрослый, который говорит с ребёнком. "
            f"Ты общаешься с ребёнком {age} лет — адаптируй стиль под его возраст."
        )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    json_data = {
        "model": "openai/gpt-4-turbo",
        "messages": messages
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=json_data) as resp:
            data = await resp.json()
            return data["choices"][0]["message"]["content"]

# Обработка обычных сообщений
@dp.message()
async def handle_message(message: Message):
    user_id = message.from_user.id
    lang = user_languages.get(user_id, "ru")  # По умолчанию — русский

    text = message.text.strip()
    age = 10  # Стандартный возраст, если не указано
    for word in text.split():
        if word.isdigit() and 3 <= int(word) <= 18:
            age = int(word)
            break

    reply = await ask_openrouter(text, age, lang)
    await message.answer(reply)

# Запуск бота
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
