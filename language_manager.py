# mrx_project/language_manager.py
import os
from vosk import Model
import torch

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# --- ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ---
_VOSK_MODEL_RU = None
# Silero TTS модель и параметры
_TTS_MODEL = None
_TTS_SPEAKER = 'eugene'
_TTS_SAMPLE_RATE = 48000

def init_language_system(llm_handler_module, prompt_module):
    """Инициализирует только русскую систему."""
    global _VOSK_MODEL_RU, _TTS_MODEL
    print("--- Инициализация языковой системы (Lite RU) ---")

    # 1. Загрузка русской модели Vosk
    try:
        # Убедитесь, что папка называется именно так
        ru_model_path = os.path.join(_PROJECT_ROOT, "vosk-model-small-ru-0.22")
        if not os.path.exists(ru_model_path):
             # Если не нашли в корне, попробуем в папке tts_models, если вы ее создавали
             ru_model_path = os.path.join(_PROJECT_ROOT, "tts_models", "vosk-model-small-ru-0.22")

        if os.path.exists(ru_model_path):
            print(f"Загрузка Vosk из: {ru_model_path}")
            _VOSK_MODEL_RU = Model(ru_model_path)
        else:
            print(f"!!! ОШИБКА: Модель Vosk не найдена по пути: {ru_model_path}")
    except Exception as e:
        print(f"!!! КРИТИЧЕСКАЯ ОШИБКА загрузки Vosk: {e}")

    # 2. Загрузка Silero TTS
    try:
        print("Загрузка Silero TTS...")
        device = torch.device('cpu')
        # Используем локальный кэш для надежности
        torch.hub.set_dir(os.path.join(_PROJECT_ROOT, 'torch_cache'))
        _TTS_MODEL, _ = torch.hub.load(repo_or_dir='snakers4/silero-models',
                                       model='silero_tts',
                                       language='ru',
                                       speaker='v3_1_ru')
        _TTS_MODEL.to(device)
    except Exception as e:
         print(f"!!! КРИТИЧЕСКАЯ ОШИБКА загрузки Silero TTS: {e}")

    # 3. Инициализация LLM
    llm_handler_module.reload_chat_session(prompt_module.PROMPTS_BY_CHARACTER['derzkiy'])
    print("--- Языковая система готова (RU) ---")

def get_current_stt_model():
    return _VOSK_MODEL_RU

def get_current_tts_params():
    # Возвращаем полный набор параметров для tts.speak
    return (_TTS_MODEL, _TTS_SPEAKER, 'ru', _TTS_SAMPLE_RATE)