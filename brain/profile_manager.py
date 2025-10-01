# brain/profile_manager.py
import json
import os

# Определяем пути относительно этого файла
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_CURRENT_DIR)
_PROFILES_ROOT_DIR = os.path.join(_PROJECT_ROOT, 'profiles')
_DRIVERS_DIR = os.path.join(_PROFILES_ROOT_DIR, 'drivers')
_CONTACTS_DIR = os.path.join(_PROFILES_ROOT_DIR, 'contacts')

# Убедимся, что все папки существуют
os.makedirs(_DRIVERS_DIR, exist_ok=True)
os.makedirs(_CONTACTS_DIR, exist_ok=True)

_current_driver_profile = None
_current_driver_name = 'guest'


# --- ФУНКЦИИ ДЛЯ РАБОТЫ С ВОДИТЕЛЯМИ ---

def load_driver_profile(profile_name):
    """Загружает профиль ВОДИТЕЛЯ и делает его активным."""
    global _current_driver_profile, _current_driver_name
    profile_path = os.path.join(_DRIVERS_DIR, f"{profile_name}.json")
    try:
        with open(profile_path, 'r', encoding='utf-8') as f:
            _current_driver_profile = json.load(f)
            _current_driver_name = profile_name
        print(f"Profile Manager: Профиль водителя '{profile_name}' успешно загружен.")
        return True
    except FileNotFoundError:
        print(f"Profile Manager WARNING: Профиль водителя '{profile_name}' не найден. Загружаю гостя.")
        return load_driver_profile('guest')
    except Exception as e:
        print(f"Profile Manager ERROR: Ошибка при загрузке профиля водителя '{profile_name}': {e}")
        return False


def create_driver_profile(profile_name):
    """Создает новый профиль ВОДИТЕЛЯ и переключается на него."""
    profile_path = os.path.join(_DRIVERS_DIR, f"{profile_name}.json")
    if os.path.exists(profile_path):
        return load_driver_profile(profile_name)

    new_profile_data = {"name": profile_name}
    with open(profile_path, 'w', encoding='utf-8') as f:
        json.dump(new_profile_data, f, ensure_ascii=False, indent=2)
    print(f"Profile Manager: Создан профиль водителя '{profile_name}'.")
    return load_driver_profile(profile_name)


def update_current_driver_profile(key, value):
    """Обновляет поле в ТЕКУЩЕМ профиле ВОДИТЕЛЯ."""
    if not _current_driver_profile or _current_driver_name == 'guest':
        print("Profile Manager WARNING: Нельзя изменять профиль гостя.")
        return False
    _current_driver_profile[key] = value
    profile_path = os.path.join(_DRIVERS_DIR, f"{_current_driver_name}.json")
    with open(profile_path, 'w', encoding='utf-8') as f:
        json.dump(_current_driver_profile, f, ensure_ascii=False, indent=2)
    print(f"Profile Manager: Профиль водителя '{_current_driver_name}' обновлен. {key} = {value}")
    return True


def get_current_driver_name():
    """Возвращает имя ТЕКУЩЕГО водителя."""
    return _current_driver_profile.get('name', 'Гость') if _current_driver_profile else 'Гость'


def get_current_driver_data():
    """Возвращает все данные ТЕКУЩЕГО водителя."""
    return _current_driver_profile


# --- ФУНКЦИИ ДЛЯ РАБОТЫ С КОНТАКТАМИ ---

def _get_contact_path(contact_name):
    """Вспомогательная функция для получения пути к файлу контакта."""
    return os.path.join(_CONTACTS_DIR, f"{contact_name}.json")


def contact_exists(contact_name):
    """Проверяет, существует ли контакт."""
    return os.path.exists(_get_contact_path(contact_name))


def create_contact(contact_name):
    """Создает файл для нового контакта."""
    if contact_exists(contact_name):
        print(f"Profile Manager INFO: Контакт '{contact_name}' уже существует.")
        return False

    contact_data = {"name": contact_name}
    try:
        with open(_get_contact_path(contact_name), 'w', encoding='utf-8') as f:
            json.dump(contact_data, f, ensure_ascii=False, indent=2)
        print(f"Profile Manager: Создан профиль контакта '{contact_name}'.")
        return True
    except Exception as e:
        print(f"Profile Manager ERROR: Не удалось создать контакт '{contact_name}': {e}")
        return False


def get_contact_info(contact_name):
    """Загружает и возвращает всю информацию о контакте."""
    if not contact_exists(contact_name):
        return None
    try:
        with open(_get_contact_path(contact_name), 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Profile Manager ERROR: Не удалось прочитать данные контакта '{contact_name}': {e}")
        return None


def update_contact_info(contact_name, key, value):
    """Добавляет или обновляет информацию в профиле контакта."""
    contact_data = get_contact_info(contact_name)
    if contact_data is None:
        return False  # Контакт не существует

    contact_data[key] = value
    try:
        with open(_get_contact_path(contact_name), 'w', encoding='utf-8') as f:
            json.dump(contact_data, f, ensure_ascii=False, indent=2)
        print(f"Profile Manager: Профиль контакта '{contact_name}' обновлен. {key} = {value}")
        return True
    except Exception as e:
        print(f"Profile Manager ERROR: Не удалось сохранить данные контакта '{contact_name}': {e}")
        return False


# --- Инициализация при запуске ---
guest_profile_path = os.path.join(_DRIVERS_DIR, 'guest.json')
if not os.path.exists(guest_profile_path):
    guest_data = {"name": "Гость", "radio_stations": {"хиты": "top hits playlist"}}
    with open(guest_profile_path, 'w', encoding='utf-8') as f:
        json.dump(guest_data, f, ensure_ascii=False, indent=2)