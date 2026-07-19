import sqlite3
import random

DB_NAME = "bot.db"

def init_db():
    """Инициализация базы данных и создание таблиц"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Таблица для пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            chat_id INTEGER PRIMARY KEY
        )
    ''')
    
    # Таблица для хадисов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hadiths (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            source TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

def add_user(chat_id: int):
    """Добавление нового пользователя, если его еще нет"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR IGNORE INTO users (chat_id) VALUES (?)", (chat_id,))
        conn.commit()
    finally:
        conn.close()

def get_all_users():
    """Получение списка всех chat_id для рассылки"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM users")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users

def get_random_hadith():
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    
    # Магия SQLite: выбираем одну абсолютно случайную строчку
    cursor.execute("SELECT text, source FROM hadiths ORDER BY RANDOM() LIMIT 1")
    row = cursor.fetchone()
    
    conn.close()
    
    # Если база вдруг пустая, вернем None, чтобы бот не упал
    if row:
        return {"text": row[0], "source": row[1]}
    return None

# Вспомогательная функция для наполнения базы (для теста)
def seed_hadiths():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    conn.close()