# mrx_project/memory/people_manager.py
import json
import os

# Определяем пути
_MEMORY_DIR = os.path.dirname(os.path.abspath(__file__))
PEOPLE_DB_PATH = os.path.join(_MEMORY_DIR, 'people_db.json')

def _load_db():
    """Загружает базу данных людей из JSON-файла."""
    if not os.path.exists(PEOPLE_DB_PATH):
        return {}
    with open(PEOPLE_DB_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def _save_db(data):
    """Сохраняет базу данных людей в JSON-файл."""
    with open(PEOPLE_DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_person_data(name):
    """Возвращает данные о конкретном человеке по имени."""
    db = _load_db()
    return db.get(name)

def add_or_update_person(name, data):
    """Добавляет нового или обновляет существующего человека в базе."""
    db = _load_db()
    # Если человек уже есть, обновляем его данные, не теряя старые
    if name in db:
        db[name].update(data)
    else:
        db[name] = data
    _save_db(db)
    print(f"[PeopleManager] Данные для '{name}' сохранены/обновлены.")

# Инициализация: создаем пустой файл, если его нет
if not os.path.exists(PEOPLE_DB_PATH):
    _save_db({})