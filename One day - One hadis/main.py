import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import os
from dotenv import load_dotenv
# Импортируем наши функции из database.py
from database import init_db, add_user, seed_hadiths, get_all_users, get_random_hadith

# Загружаем переменные из файла .env
load_dotenv()

# Достаем токен безопасности
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)

# Настраиваем логирование, чтобы видеть ошибки в консоли
logging.basicConfig(level=logging.INFO)
dp = Dispatcher()
scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    user_id = message.chat.id
    add_user(user_id) # Сохраняем пользователя в БД
    
    await message.answer(
        f"Здравствуй, {message.from_user.full_name}! 👋\n\n"
        "Добро пожаловать в бот «One day - one hadis».\n"
        "Каждый день вы будете получать один случайный достоверный хадис."
    )

async def send_daily_hadith():
    """Функция ежедневной рассылки всем пользователям"""
    hadith = get_random_hadith()
    if not hadith:
        return # Если в базе нет хадисов, ничего не делаем
    
    text, source = hadith
    message_text = f"📖 **Хадис дня:**\n\n{hadith['text']}\n\n📌 *Источник:* {hadith['source']}"
    
    user_ids = get_all_users()
    for user_id in user_ids:
        try:
            # Используем parse_mode="Markdown" для красивого текста
            await bot.send_message(chat_id=user_id, text=message_text, parse_mode="Markdown")
            # Небольшая пауза между отправками, чтобы Telegram нас не заблокировал за спам
            await asyncio.sleep(0.05)
        except Exception as e:
            print(f"Не удалось отправить сообщение пользователю {user_id}: {e}")

async def main():
    # Инициализируем БД и наполняем тестовыми данными
    init_db()
    seed_hadiths()
    
    # Настраиваем планировщик (отправка каждый день, например, в 09:00 утра)
    # Для теста можно поменять hours=9, minutes=0 на seconds=30, чтобы проверить сразу
    scheduler.add_job(send_daily_hadith, trigger="cron",
    hour=9,
    minute=0,
    timezone="Europe/Moscow")
    scheduler.start()
    
    # Запускаем чтение обновлений от Telegram (Polling)
    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())