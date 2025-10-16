# mrx_project/language_manager.py
import fasttext
import vosk
import torch
import sounddevice as sd
import os

# --- Умное определение пути к модели ---
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# --- Настройки ---
# Модель для определения языка (lid.176.bin должна лежать в корне проекта)
LANG_MODEL_PATH = os.path.join(_PROJECT_ROOT, 'lid.176.bin')

# Словарь с настройками для каждого языка
# ВНИМАНИЕ: Убедитесь, что у вас есть модели vosk-model-small-uz-0.22 и silero_model_id для узбекского,
# а также что соответствующий спикер (например, 'dilnoza') существует в Silero для этого языка.
# Возможно, для узбекского языка вам понадобится другая Silero-модель или другая версия.
# Для примера я оставил 'v3_1_ru' и 'baya' для узбекского, но это нужно будет изменить!
LANG_CONFIG = {
    'ru': {
        'vosk_model_path': os.path.join(_PROJECT_ROOT, 'vosk-model-small-ru-0.22'),
        'silero_model_id': 'v3_1_ru', # Для русского используем ru модель Silero
        'silero_speaker': 'eugene', # Или 'aidar', 'kseniya', 'natasha', 'xenia', 'eugene'
        'tts_lang': 'ru',
        'silero_sample_rate': 48000,
        'system_prompt_key': 'SYSTEM_PROMPT_RU_DERZKIY',
    },
    'uz': {
        'vosk_model_path': os.path.join(_PROJECT_ROOT, 'vosk-model-small-uz-0.22'),
        'silero_model_id': 'v3_uz', # <<< ЭТО НУЖНО ЗАМЕНИТЬ НА УЗБЕКСКУЮ МОДЕЛЬ SILERO, ЕСЛИ ОНА ЕСТЬ
        'silero_speaker': 'dilnavoz',
        'tts_lang': 'uz',
        'silero_sample_rate': 48000,
        'system_prompt_key': 'SYSTEM_PROMPT_UZ',
    }
}

# --- Глобальные переменные для текущих активных моделей ---
_current_lang = 'ru'
_current_vosk_model = None
_current_tts_model = None
_current_tts_speaker = None
_current_tts_lang = None
_current_tts_sample_rate = None
_current_system_prompt = None

# Загружаем модель определения языка
try:
    print(f"Загрузка модели FastText для определения языка из: {LANG_MODEL_PATH}")
    lang_detector = fasttext.load_model(LANG_MODEL_PATH)
except ValueError:
    print(f"ОШИБКА: Не удалось загрузить модель FastText по пути '{LANG_MODEL_PATH}'.")
    print("Убедитесь, что 'lid.176.bin' скачан и находится в корне проекта.")
    exit()

# Устройство для Silero TTS
_tts_device = torch.device('cpu') # Или 'cuda' если есть GPU

def _load_vosk_model(path, lang_code):
    """Вспомогательная функция для загрузки модели Vosk."""
    try:
        print(f"Загрузка Vosk модели из: {path}")
        model = vosk.Model(path)
        # --- ВОТ ИСПРАВЛЕНИЕ ---
        # Мы сами создаем атрибут lang_name и присваиваем ему код языка
        model.lang_name = lang_code.upper()
        return model
    except Exception as e:
        print(f"ОШИБКА: Не удалось найти или загрузить Vosk модель по пути '{path}'.")
        print("Убедитесь, что вы скачали, распаковали и положили ее в корень проекта.")
        print(e)
        exit()

def _load_silero_tts_model(model_id, lang):
    """Вспомогательная функция для загрузки модели Silero TTS."""
    try:
        print(f"Загрузка Silero TTS модели (ID: {model_id}, Lang: {lang})")
        # Здесь мы загружаем общую Silero TTS модель, которая поддерживает разные языки и спикеров.
        # Если для узбекского нужна СОВЕРШЕННО другая модель (не просто другой speaker/lang),
        # то model_id в LANG_CONFIG для 'uz' должен быть другим.
        model, _ = torch.hub.load(repo_or_dir='snakers4/silero-models',
                                  model='silero_tts',
                                  language=lang, # Этот параметр влияет на то, какую модель Silero загружает
                                  speaker=model_id) # Это speaker ID модели, а не конкретный спикер
        model.to(_tts_device)
        return model
    except Exception as e:
        print(f"ОШИБКА: Не удалось загрузить Silero TTS модель (ID: {model_id}, Lang: {lang}).")
        print(f"Возможно, неверный model_id или язык не поддерживается. Ошибка: {e}")
        exit()

def init_language_system(llm_handler_module, prompt_module):
    """Инициализирует языковую систему, загружая модели по умолчанию (русский)."""
    global _current_vosk_model, _current_tts_model, _current_tts_speaker, \
           _current_tts_lang, _current_tts_sample_rate, _current_system_prompt

    print("Инициализация языковой системы MRX...")

    # Устанавливаем русский по умолчанию
    _current_lang = 'ru'
    config = LANG_CONFIG[_current_lang]

    # Загружаем Vosk модель
    _current_vosk_model = _load_vosk_model(config['vosk_model_path'], _current_lang)

    # Загружаем Silero TTS модель
    _current_tts_model = _load_silero_tts_model(config['silero_model_id'], config['tts_lang'])
    _current_tts_speaker = config['silero_speaker']
    _current_tts_lang = config['tts_lang']
    _current_tts_sample_rate = config['silero_sample_rate']

    # Загружаем системный промпт
    _current_system_prompt = getattr(prompt_module, config['system_prompt_key'])
    llm_handler_module.reload_chat_session(_current_system_prompt)

    print(f"Языковая система инициализирована. Текущий язык: {_current_lang.upper()}")


def detect_language(text):
    """Определяет язык текста."""
    if not text:
        return _current_lang # Возвращаем текущий, если нет текста

    # fasttext возвращает кортеж типа ('__label__ru',), нам нужно извлечь 'ru'
    predictions = lang_detector.predict(text.lower(), k=1)
    lang_code = predictions[0][0].replace('__label__', '')
    return lang_code

def get_current_stt_model():
    """Возвращает текущую модель Vosk для распознавания речи."""
    return _current_vosk_model

def get_current_tts_params():
    """Возвращает параметры для Silero TTS: модель, спикера, язык, частоту."""
    return _current_tts_model, _current_tts_speaker, _current_tts_lang, _current_tts_sample_rate


def switch_language(lang_code, llm_handler_module, prompt_module):
    """Переключает язык системы."""
    global _current_lang, _current_vosk_model, _current_tts_model, \
           _current_tts_speaker, _current_tts_lang, _current_tts_sample_rate, \
           _current_system_prompt

    if lang_code not in LANG_CONFIG:
        print(f"ПРЕДУПРЕЖДЕНИЕ: Язык '{lang_code}' не поддерживается. Остаюсь на {_current_lang.upper()}.")
        return False

    if _current_lang != lang_code:
        print(f"--- Переключаю язык на: {lang_code.upper()} ---")
        _current_lang = lang_code
        config = LANG_CONFIG[_current_lang]

        # Перезагружаем Vosk модель
        _current_vosk_model = _load_vosk_model(config['vosk_model_path'], _current_lang)

        # Перезагружаем Silero TTS модель
        _current_tts_model = _load_silero_tts_model(config['silero_model_id'], config['tts_lang'])
        _current_tts_speaker = config['silero_speaker']
        _current_tts_lang = config['tts_lang']
        _current_tts_sample_rate = config['silero_sample_rate']

        # Обновляем системный промпт для LLM
        _current_system_prompt = getattr(prompt_module, config['system_prompt_key'])
        llm_handler_module.reload_chat_session(_current_system_prompt)

        return True
    return False

# Тестовая секция для проверки FastText, если запустить файл напрямую
if __name__ == '__main__':
    print("Тестирование language_manager...")
    test_texts = [
        "Привет, как дела?",
        "Salom, ishlaring qanday?",
        "Hello, how are you?",
        "Что-то скучновато. Рассказать анекдот?",
        "Oynalarni yarmigacha tushir"
    ]
    for text in test_texts:
        lang = detect_language(text)
        print(f"Текст: '{text}' -> Определенный язык: {lang}")

    # Это имитация инициализации, полная инициализация происходит в main.py
    # init_language_system()
    # switch_language('uz')