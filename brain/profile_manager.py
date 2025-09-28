# brain/profile_manager.py
import json
import os

# Определяем пути относительно этого файла
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_CURRENT_DIR) # Поднимаемся на уровень вверх (в папку MRX)
_PROFILES_DIR = os.path.join(_PROJECT_ROOT, 'profiles')

# Убедимся, что папка для профилей существует
os.makedirs(_PROFILES_DIR, exist_ok=True)

_current_profile = None

def load_profile(profile_name):
    """Загружает профиль водителя из JSON-файла."""
    global _current_profile
    profile_path = os.path.join(_PROFILES_DIR, f"{profile_name}.json")
    try:
        with open(profile_path, 'r', encoding='utf-8') as f:
            _current_profile = json.load(f)
        print(f"Profile Manager: Профиль '{profile_name}' успешно загружен.")
        return True
    except FileNotFoundError:
        print(f"Profile Manager ERROR: Профиль '{profile_name}.json' не найден в папке '{_PROFILES_DIR}'.")
        # Загружаем профиль гостя, если основной не найден
        return load_profile('guest')
    except Exception as e:
        print(f"Profile Manager ERROR: Ошибка при загрузке профиля: {e}")
        return False

def get_current_driver_name():
    """Возвращает имя текущего водителя."""
    if _current_profile:
        return _current_profile.get('name', 'Гость')
    return 'Гость'

def get_profile_data(key):
    """Возвращает данные из текущего профиля по ключу (например, 'home_address')."""
    if _current_profile:
        return _current_profile.get(key)
    return None

def get_radio_stations():
    """Возвращает словарь с радиостанциями из текущего профиля."""
    if _current_profile:
        return _current_profile.get('radio_stations')
    return None

# Создадим профиль гостя по умолчанию, если его нет
guest_profile_path = os.path.join(_PROFILES_DIR, 'guest.json')
if not os.path.exists(guest_profile_path):
    guest_data = {
        "name": "Гость",
        "radio_stations": {
            "хиты": "top hits playlist"
        }
    }
    with open(guest_profile_path, 'w', encoding='utf-8') as f:
        json.dump(guest_data, f, ensure_ascii=False, indent=2)