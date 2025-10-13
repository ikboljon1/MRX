# mrx_project/voice/wake_word_detector.py
import os
import struct
import pvporcupine
import pyaudio

# --- НАСТРОЙКИ ---
# ВАЖНО: Замените 'YOUR_ACCESS_KEY_HERE' на ваш ключ с сайта Picovoice
PICOVOICE_ACCESS_KEY = 'Kq9p+6JYSBoKPZgkCnnMoMrksDvQ7tKtVf0OVDwgYVf/2ODLej/R/w=='

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_WAKE_WORDS_DIR = os.path.join(_PROJECT_ROOT, 'wake_words')

# Автоматически находим все .ppn файлы в папке
KEYWORD_PATHS = [os.path.join(_WAKE_WORDS_DIR, f) for f in os.listdir(_WAKE_WORDS_DIR) if f.endswith('.ppn')]

# --- ГЛОБАЛЬНАЯ ПЕРЕМЕННАЯ ДЛЯ ДЕТЕКТОРА ---
porcupine = None
pa = None
audio_stream = None


def initialize_detector():
    """Инициализирует Porcupine и аудиопоток."""
    global porcupine, pa, audio_stream
    try:
        if not KEYWORD_PATHS:
            raise ValueError("Не найдены файлы моделей .ppn в папке wake_words")
        if PICOVOICE_ACCESS_KEY == 'YOUR_ACCESS_KEY_HERE':
            raise ValueError("Не указан PICOVOICE_ACCESS_KEY в wake_word_detector.py")

        porcupine = pvporcupine.create(
            access_key=PICOVOICE_ACCESS_KEY,
            keyword_paths=KEYWORD_PATHS
        )

        pa = pyaudio.PyAudio()
        audio_stream = pa.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length
        )
        print("Детектор активационного слова (Porcupine) готов.")
        print(f"Ожидаю слова: {[os.path.basename(p).split('_')[0] for p in KEYWORD_PATHS]}")

    except Exception as e:
        print(f"КРИТИЧЕСКАЯ ОШИБКА при инициализации Porcupine: {e}")


def listen_for_wake_word():
    """
    Блокирующая функция. Слушает аудиопоток и возвращает True, как только услышит активационное слово.
    """
    if not porcupine or not audio_stream:
        print("ОШИБКА: Детектор не был инициализирован.")
        return False

    while True:
        pcm = audio_stream.read(porcupine.frame_length)
        pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

        keyword_index = porcupine.process(pcm)
        if keyword_index >= 0:
            print(">>> Активационное слово услышано!")
            return True


def shutdown_detector():
    """Корректно освобождает ресурсы."""
    global porcupine, pa, audio_stream
    if audio_stream is not None:
        audio_stream.close()
    if pa is not None:
        pa.terminate()
    if porcupine is not None:
        porcupine.delete()
    print("Детектор активационного слова выключен.")