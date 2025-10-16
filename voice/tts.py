# mrx_project/voice/tts.py
import torch
import sounddevice as sd
import time

# Глобальная переменная для устройства
_tts_device = torch.device('cpu')


def speak(model, text, speaker='eugene', sample_rate=48000):
    """
    Преобразует текст в речь и воспроизводит его.
    Теперь принимает модель и текст как основные аргументы.
    """
    if not text:
        return
    if model is None:
        print("ОШИБКА: Silero TTS модель не загружена. Не могу говорить.")
        return

    # Изменили логгер, чтобы он явно показывал спикера
    print(f"MRX ({speaker}) произносит: {text}")

    gen_start_time = time.perf_counter()

    try:
        audio = model.apply_tts(text=text,
                                speaker=speaker,
                                sample_rate=sample_rate,
                                put_accent=True,
                                put_yo=True)

        gen_end_time = time.perf_counter()
        gen_duration = gen_end_time - gen_start_time
        print(f"[PERF] TTS Generation took: {gen_duration:.4f} seconds")

        sd.play(audio, samplerate=sample_rate)
        sd.wait()

    except Exception as e:
        print(f"!!! ОШИБКА TTS: Не удалось синтезировать речь: {e}")
        # Это может случиться, если LLM вернет текст с неподдерживаемыми символами
        # или если модель TTS не сможет его обработать.