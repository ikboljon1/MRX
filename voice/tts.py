# mrx_project/voice/tts.py
import torch
import sounddevice as sd
import time  # <-- ДОБАВЛЯЕМ ИМПОРТ

# Глобальная переменная для устройства
_tts_device = torch.device('cpu')  # Или 'cuda' если есть GPU


def speak(tts_model_obj, speaker_name, lang_code, text, sample_rate=48000):
    """
    Преобразует текст в речь и воспроизводит его, измеряя время генерации.
    """
    if not text:
        return
    if tts_model_obj is None:
        print("ОШИБКА: Silero TTS модель не загружена. Не могу говорить.")
        return

    print(f"MRX произносит ({lang_code}, {speaker_name}): {text}")

    # --- ИЗМЕРЕНИЕ ВРЕМЕНИ ГЕНЕРАЦИИ ---
    gen_start_time = time.perf_counter()

    audio = tts_model_obj.apply_tts(text=text,
                                    speaker=speaker_name,
                                    sample_rate=sample_rate,
                                    put_accent=True,
                                    put_yo=True)

    gen_end_time = time.perf_counter()
    gen_duration = gen_end_time - gen_start_time
    print(f"[PERF] TTS Generation took: {gen_duration:.4f} seconds")
    # ------------------------------------

    sd.play(audio, samplerate=sample_rate)
    sd.wait()