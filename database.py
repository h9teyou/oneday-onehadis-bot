import sqlite3

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
    
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN preferred_hour INTEGER DEFAULT 9")
    except sqlite3.OperationalError:
        pass
    
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
    """Добавление нового пользователя"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR IGNORE INTO users (chat_id) VALUES (?)", (chat_id,))
        conn.commit()
    finally:
        conn.close()

def get_random_hadith():
    """Возвращает один случайный хадис в виде кортежа (text, source)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT text, source FROM hadiths ORDER BY RANDOM() LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return row if row else None

def get_all_id():
    """Возвращает общее количество пользователей"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

def user_time_hour(chat_id: int, hour: int):
    """Обновляет время рассылки для пользователя"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET preferred_hour = ? WHERE chat_id = ?", (hour, chat_id))
    conn.commit()
    conn.close()

def get_users_by_hour(hour: int):
    """Возвращает список chat_id пользователей для указанного часа"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()  
    cursor.execute("SELECT chat_id FROM users WHERE preferred_hour = ?", (hour,))
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def seed_hadiths():
    """Вспомогательная функция для тестового наполнения базы (если она пустая)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM hadiths")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO hadiths (text, source) VALUES (?, ?)",
            ("Поистине, дела оцениваются только по намерениям...", "Сахих аль-Бухари")
        )
        conn.commit()
    conn.close()
    
    
def get_all_users():
    """Достаю все chat_id для админской рассылки"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM users")
    rows = cursor.fetchall()
    conn.close()
    return[row[0] for row in rows]


def search_hadith(query, limit=5):
    """Ищет хадисы по определённым словам"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT text, source FROM hadiths WHERE text LIKE ? LIMIT ?", 
        (f"%{query}%", limit)
    )
    
    results = cursor.fetchall()
    conn.close()
    return results