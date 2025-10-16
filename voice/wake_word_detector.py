# mrx_project/voice/wake_word_detector.py
import asyncio
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
    Блокирующая функция, которая слушает аудиопоток до тех пор,
    пока не будет обнаружено активационное слово.
    Предназначена для вызова из синхронного кода или через run_in_executor.
    """
    # Мы не передаем media_player, так как в этой простой версии
    # мы не можем управлять им. Пауза музыки обрабатывается в `run_detector_in_background`.
    # Для простого ожидания слова этого достаточно.
    if not porcupine or not audio_stream:
        print("ОШИКА: Детектор не инициализирован.")
        return

    try:
        while True:
            pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

            keyword_index = porcupine.process(pcm)
            if keyword_index >= 0:
                print(">>> Активационное слово услышано! (из listen_for_wake_word)")
                return # Выходим из функции, когда слово найдено
    except KeyboardInterrupt:
        print("Остановка ожидания активационного слова.")
        return


async def run_detector_in_background(wake_word_event, media_player_module, loop):
    """
    Главная функция для фоновой задачи. Вечно слушает активационное слово.
    """
    print("[WAKE_WORD] Фоновый детектор запущен.")
    while True:
        # Запускаем блокирующий код в отдельном потоке, чтобы не морозить asyncio
        found = await loop.run_in_executor(None, _listen_and_process_frame, media_player_module)
        if found:
            # Отправляем сигнал основному циклу, что пора начинать диалог
            wake_word_event.set()
        # Даем другим задачам шанс выполниться
        await asyncio.sleep(0.01)


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