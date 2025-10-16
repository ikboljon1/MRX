# mrx_project/brain/offline_handler.py
from rapidfuzz import process, fuzz

# Расширяем словарь команд, добавляя управление автомобилем.
# Для каждой команды указываем ключевые слова и порог уверенности.
OFFLINE_COMMANDS = {
    # --- Сетевые команды ---
    'network_check_status': {
        'keywords': ['проверь интернет', 'проверь соединение', 'есть интернет'],
        'threshold': 85
    },
    'network_scan_wifi': {
        'keywords': ['проверь вайфай', 'найди сети', 'поищи вайфай', 'сканируй сети'],
        'threshold': 90
    },
    'network_connect_wifi': {
        'keywords': ['подключись к вайфай', 'подключи вайфай', 'подключись к сети'],
        'threshold': 85,
        'response': "К какой сети подключиться?"  # Ответ-вопрос
    },

    # --- Команды управления автомобилем ---
    'ac_toggle': {
        'keywords': ['кондиционер', 'климат', 'печку', 'включи холод', 'включи тепло'],
        'threshold': 80,
        'response': "Выполняю."
    },
    'doors_lock': {
        'keywords': ['закрой двери', 'заблокируй замки', 'закрой машину'],
        'threshold': 90,
        'response': "Двери заблокированы."
    },
    'doors_unlock': {
        'keywords': ['открой двери', 'разблокируй замки', 'открой машину'],
        'threshold': 90,
        'response': "Двери разблокированы."
    },
    'hazard_lights_toggle': {
        'keywords': ['аварийка', 'аварийная сигнализация', 'моргалки'],
        'threshold': 85,
        'response': "Включаю аварийку."
    },
    'window_all_down_100': {
        'keywords': ['открой все окна', 'опусти все окна', 'открыть окна'],
        'threshold': 88,
        'response': "Открываю все окна."
    },
    'window_all_up_100': {
        'keywords': ['закрой все окна', 'подними все окна', 'закрыть окна'],
        'threshold': 88,
        'response': "Закрываю все окна."
    },
    'window_left_down_100': {
        'keywords': ['открой левое окно', 'опусти левое окно'],
        'threshold': 90,
        'response': "Открываю левое окно."
    },
    'window_left_up_100': {
        'keywords': ['закрой левое окно', 'подними левое окно'],
        'threshold': 90,
        'response': "Закрываю левое окно."
    },
    # Можно добавить и правое окно по аналогии
}


def recognize_command(text):
    """
    Ищет в тексте ключевые слова для ОФФЛАЙН команд, используя нечеткий поиск.
    Возвращает словарь с командой или None.
    """
    text_lower = text.lower()

    # Создаем один большой список всех ключевых слов для поиска
    all_keywords = []
    for command, data in OFFLINE_COMMANDS.items():
        for keyword in data['keywords']:
            all_keywords.append(keyword)

    # Ищем наиболее похожее ключевое слово во всем тексте
    # extractOne вернет (найденное_слово, уровень_схожести, индекс)
    best_match = process.extractOne(text_lower, all_keywords, scorer=fuzz.partial_ratio)

    if not best_match or best_match[1] < 75:  # Базовый порог, чтобы отсечь совсем мусор
        return None

    found_keyword = best_match[0]

    # Теперь ищем, какой команде принадлежит найденное ключевое слово
    for command, data in OFFLINE_COMMANDS.items():
        if found_keyword in data['keywords']:
            # Проверяем, достаточна ли уверенность для этой конкретной команды
            if best_match[1] > data['threshold']:
                print(f"[OFFLINE] Распознана оффлайн команда: '{command}' (схожесть: {best_match[1]}%)")
                return {
                    'command': command,
                    'response': data.get('response', 'Выполняю.')  # .get() для безопасности
                }

    return None