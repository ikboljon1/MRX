# mrx_project/voice/tts.py
import torch
import sounddevice as sd

# Глобальная переменная для устройства, загружать здесь, а не в функции
_tts_device = torch.device('cpu') # Или 'cuda' если есть GPU

def speak(tts_model_obj, speaker_name, lang_code, text, sample_rate=48000):
    """
    Преобразует текст в речь и воспроизводит его, используя заданную модель и параметры.
    """
    if not text:
        return
    if tts_model_obj is None:
        print("ОШИБКА: Silero TTS модель не загружена. Не могу говорить.")
        return

    # Мы оставляем lang_code в аргументах функции для удобства логирования
    print(f"MRX произносит ({lang_code}, {speaker_name}): {text}")

    audio = tts_model_obj.apply_tts(text=text,
                                    speaker=speaker_name,
                                    # Аргумент language здесь не нужен, убираем его
                                    sample_rate=sample_rate,
                                    put_accent=True,
                                    put_yo=True)

    sd.play(audio, samplerate=sample_rate)
    sd.wait()
# Тест, если запустить файл напрямую - УДАЛЯЕМ, так как модель теперь загружается извне
# if __name__ == '__main__':
#     print("Этот модуль не запускается напрямую для тестирования TTS-модели.")
#     print("Используйте main.py для полноценного тестирования.")