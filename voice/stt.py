# mrx_project/voice/stt.py
import vosk
import sounddevice as sd
import json
import queue
import os # <-- Импортируем модуль os

# --- Умное определение пути к модели ---
# Получаем путь к директории, где лежит ЭТОТ файл (voice/)
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Поднимаемся на один уровень вверх, чтобы попасть в корень проекта (mrx_project/)
_PROJECT_ROOT = os.path.dirname(_CURRENT_DIR)
# Собираем полный, абсолютный путь к папке с моделью
MODEL_PATH = os.path.join(_PROJECT_ROOT, "vosk-model-small-ru-0.22")

# Частота дискретизации, важна для Vosk
SAMPLE_RATE = 16000
# ID вашего микрофона (None - по умолчанию)
DEVICE_ID = None

# Проверяем, существует ли модель
try:
    print(f"Загрузка модели Vosk из: {MODEL_PATH}") # Добавим отладочный вывод
    model = vosk.Model(MODEL_PATH)
except Exception:
    print(f"ОШИБКА: Не удалось найти модель Vosk по пути '{MODEL_PATH}'.")
    print("Убедитесь, что вы скачали, распаковали и положили ее в корень проекта.")
    exit()

q = queue.Queue()


def callback(indata, frames, time, status):
    """Эта функция вызывается для каждого блока аудио с микрофона."""
    if status:
        print(status, flush=True)
    q.put(bytes(indata))


def listen():
    """
    Слушает микрофон до тех пор, пока не будет распознана полная фраза.
    Возвращает распознанный текст.
    """
    recognizer = vosk.KaldiRecognizer(model, SAMPLE_RATE)
    print("\nСлушаю...")

    with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=8000, device=DEVICE_ID,
                           dtype='int16', channels=1, callback=callback):

        while True:
            data = q.get()
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get('text', '')
                if text:  # Если что-то распознано
                    print(f"Распознано: '{text}'")
                    return text