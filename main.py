import asyncio
import logging
import os
import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, FSInputFile
from aiogram.filters import CommandStart, Command, CommandObject
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

# Импортируем чистые функции из базы
from database import (
    init_db, add_user, seed_hadiths, 
    get_random_hadith, get_all_id, 
    get_users_by_hour, user_time_hour,
    get_all_users, search_hadith
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 6602711679

bot = Bot(token=BOT_TOKEN)
logging.basicConfig(level=logging.INFO)
dp = Dispatcher()
scheduler = AsyncIOScheduler(timezone="Europe/Moscow")


def get_main_menu_keyboard():
    """Возвращает инлайн-клавиатуру главного меню"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎲 Случайный хадис", callback_data="btn_random")
            ],
            [
                InlineKeyboardButton(text="⏰ Выбрать время рассылки", callback_data="btn_time")
            ],
            [
                InlineKeyboardButton(text="🔍 Поиск по хадисам", callback_data="btn_search")
            ]
        ]
    )
    return keyboard

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    user_id = message.chat.id
    add_user(user_id)
    

    photo = FSInputFile("picsart.jpg")

    caption_text = (
        f"Здравствуй, {message.from_user.full_name}! 👋\n\n"
        "Добро пожаловать в бот «One day - one hadis».\n"
        "Каждый день вы будете получать один случайный достоверный хадис.\n\n"
        "Воспользуйтесь меню ниже для управления ботом 👇"
    )
 

    await message.answer_photo(
        photo=photo,
        caption=caption_text,
        reply_markup=get_main_menu_keyboard()
    )

@dp.message(Command("broadcast"))
async def cmd_broadcast(message: types.Message, command: CommandObject):
    if message.from_user.id != ADMIN_ID:
        return

    text_to_send = command.args

    if not text_to_send:
        await message.answer(
            "⚠️ **Вы не ввели текст для рассылки!**\n\n"
            "**Как использовать:**\n"
            "`/broadcast Ваш текст рассылки здесь`",
            parse_mode="Markdown"
        )
        return

    users = get_all_users()
    
    status_msg = await message.answer(f"🚀 **Рассылка запущена!**\nВсего получателей: {len(users)}")
    
    success_count = 0
    failed_count = 0

    for user_id in users:
        try:
            await bot.send_message(chat_id=user_id, text=text_to_send)
            success_count += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed_count += 1

    await status_msg.edit_text(
        f"✅ **Рассылка успешно завершена!**\n\n"
        f"📬 Доставлено: **{success_count}**\n"
        f"❌ Не доставлено (заблокировали бота): **{failed_count}**",
        parse_mode="Markdown"
    )

@dp.message(Command("random"))
async def cmd_random(message: types.Message):
    hadith = get_random_hadith()
    if not hadith:
        await message.answer("База данных пока пуста 😔")
        return
    
    text, source = hadith[0], hadith[1]
    an_text = f"✨ **Случайный хадис:**\n\n{text}\n\n_📌 Источник: {source}_"
    await message.answer(an_text, parse_mode="Markdown")

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    countusers = get_all_id()
    texttome = f"📊 **Статистика бота:**\n\nВсего подписчиков: {countusers}"
    await message.answer(texttome, parse_mode="Markdown")

@dp.message(Command("time"))
async def cmd_time(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🌅 09:00 Утра", callback_data="set_time_9"),
                InlineKeyboardButton(text="☀️ 14:00 Обед", callback_data="set_time_14"),
            ],
            [
                InlineKeyboardButton(text="🌙 20:00 Вечер", callback_data="set_time_20"),
            ]
        ]
    )
    await message.answer("Выберите удобное время для получения ежедневного хадиса (по МСК):", reply_markup=keyboard)

@dp.callback_query(F.data.startswith("set_time_"))
async def process_time_selection(callback: CallbackQuery):
    hour = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    user_time_hour(user_id, hour)
    
    await callback.answer(f"Время изменено на {hour}:00!")
    await callback.message.edit_text(f"✅ Теперь хадисы будут приходить каждый день в **{hour}:00** по МСК.", parse_mode="Markdown")
    
@dp.message(Command("search"))
async def cmd_search(message: types.Message, command: CommandObject):
    query = command.args
    
    if not query:
        await message.answer(
            "🔍 **Поиск по хадисам**\n\n"
            "Напишите слово для поиска после команды, например:\n"
            "`/search намерение`\n"
            "`/search молитва`\n"
            "`/search терпение`",
            parse_mode="Markdown"
        )
        return
    
    results = search_hadith(query, limit=3)
    
    if not results:
        await message.answer(
            f"🔍 По запросу **«{query}»** ничего не найдено.\n"
            f"Попробуйте ввести другое слово или его корень.",
            parse_mode="Markdown"
        )
        return
    
    await message.answer(f"🔍 **Результаты поиска по запросу «{query}»:**", parse_mode="Markdown")
    
    for text, source in results:
        response_text = f"📖 {text}\n\n📌 *Источник:* {source}"
        await message.answer(response_text, parse_mode="Markdown")
        await asyncio.sleep(0.1)
        
@dp.callback_query(F.data == "btn_random")
async def process_btn_random(callback: CallbackQuery):
    hadith = get_random_hadith()
    if not hadith:
        await callback.answer("База данных пока пуста 😔", show_alert=True)
        return
    
    text, source = hadith[0], hadith[1]
    an_text = f"✨ **Случайный хадис:**\n\n{text}\n\n_📌 Источник: {source}_"
    
    await callback.answer()  # Убираем "часики" загрузки на кнопке
    await callback.message.answer(an_text, parse_mode="Markdown")


@dp.callback_query(F.data == "btn_time")
async def process_btn_time(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🌅 09:00 Утра", callback_data="set_time_9"),
                InlineKeyboardButton(text="☀️ 14:00 Обед", callback_data="set_time_14"),
            ],
            [
                InlineKeyboardButton(text="🌙 20:00 Вечер", callback_data="set_time_20"),
            ]
        ]
    )
    await callback.answer()
    await callback.message.answer("Выберите удобное время для получения ежедневного хадиса (по МСК):", reply_markup=keyboard)


@dp.callback_query(F.data == "btn_search")
async def process_btn_search(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "🔍 **Поиск по хадисам**\n\n"
        "Напишите слово или его часть после команды `/search`, например:\n"
        "`/search молитв`\n"
        "`/search терпен`\n\n"
        "💡 *Совет:* вводите корень слова, чтобы бот находил варианты во всех формах!",
        parse_mode="Markdown"
    )

async def send_hourly_hadiths():
    """Ежечасовая проверка: отправляет хадис только тем, у кого выбран текущий час"""
    current_hour = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).hour
    users_to_send = get_users_by_hour(current_hour)
    
    if not users_to_send:
        return
        
    hadith = get_random_hadith()
    if not hadith:
        return
        
    message_text = f"📖 **Хадис дня:**\n\n{hadith[0]}\n\n📌 *Источник:* {hadith[1]}"
    
    for user_id in users_to_send:
        try:
            await bot.send_message(chat_id=user_id, text=message_text, parse_mode="Markdown")
            await asyncio.sleep(0.05)
        except Exception as e:
            print(f"Не удалось отправить пользователю {user_id}: {e}")

async def main():
    init_db()
    seed_hadiths()
    
    # Каждая минута 00 каждого часа запуск проверки
    scheduler.add_job(send_hourly_hadiths, trigger="cron", minute=0, timezone="Europe/Moscow")
    
    scheduler.start()
    
    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())