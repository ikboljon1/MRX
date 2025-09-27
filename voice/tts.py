# mrx_project/voice/tts.py
import torch
import sounddevice as sd

print("Инициализация TTS-модели (Silero)...")

language = 'ru'
model_id = 'v3_1_ru'
device = torch.device('cpu')

model, _ = torch.hub.load(repo_or_dir='snakers4/silero-models',
                          model='silero_tts',
                          language=language,
                          speaker=model_id)
model.to(device)

# При первом запуске модель скачается, это может занять время.
print("TTS-модель готова.")


def speak(text):
    """
    Преобразует текст в речь и воспроизводит его.
    """
    if not text:
        return

    print(f"MRX произносит: {text}")

    # 'baya' - один из доступных голосов. Другие варианты: 'aidar', 'kseniya'
    audio = model.apply_tts(text=text,
                            speaker='baya',
                            sample_rate=48000,
                            put_accent=True,
                            put_yo=True)

    sd.play(audio, samplerate=48000)
    sd.wait()  # Ждем, пока речь не закончится


# Тест, если запустить файл напрямую
if __name__ == '__main__':
    speak("Привет, я Лиза. Проверка голосового модуля один, два, три.")