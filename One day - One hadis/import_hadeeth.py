import json
import sqlite3

def import_raw_json():
    # 1. Открываем сырой файл от HadeethEnc
    try:
        with open("hadeeth_raw.json", "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        print("❌ Ошибка: Файл hadeeth_raw.json не найден в папке проекта!")
        return

    hadiths_to_db = []

    print("⏳ Начинаю разбор и очистку хадисов...")
    
    for item in data:
        # Достаем текст хадиса (Column5)
        text = item.get("Column5")
        
        # Достаем источник (Column13) и убираем некрасивые квадратные скобки [ ]
        source_raw = item.get("Column13", "")
        source_cleaned = source_raw.replace("[", "").replace("]", "")
        
        # Извлекаем уникальный ID хадиса из ссылки в Column15
        url = item.get("Column15", "")
        hadith_id = url.split("/")[-1] if url else ""
        
        # Собираем красивый точный источник по нашему шаблону
        if hadith_id and source_cleaned:
            source = f"{source_cleaned} (№ {hadith_id})"
        else:
            source = source_cleaned

        # Если в этой строке есть и текст, и источник — добавляем в список для базы
        if text and source:
            hadiths_to_db.append((text.strip(), source.strip()))

    if not hadiths_to_db:
        print("❌ Не удалось извлечь хадисы. Проверь структуру JSON-файла.")
        return

    # 2. Подключаемся к базе данных бота
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    
    # На всякий случай очистим старые тестовые хадисы, если они там были
    cursor.execute("DELETE FROM hadiths")
    
    # 3. Закидываем весь массив одной быстрой транзакцией
    cursor.executemany(
        "INSERT INTO hadiths (text, source) VALUES (?, ?)",
        hadiths_to_db
    )
    
    conn.commit()
    conn.close()
    
    print(f"🎉 Ура! База данных успешно заполнена!")
    print(f"📚 Всего добавлено достоверных хадисов: {len(hadiths_to_db)}")

if __name__ == "__main__":
    import_raw_json()