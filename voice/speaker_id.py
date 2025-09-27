# mrx_project/voice/speaker_id.py

from resemblyzer import VoiceEncoder, preprocess_wav
from pathlib import Path
import numpy as np
import json
import os
import sounddevice as sd
import wavio  # Эта библиотека установилась вместе с resemblyzer

# --- Настройки ---
PROFILES_DIR = "profiles"
SAMPLE_RATE = 16000  # Должно совпадать с Vosk
ENCODER = VoiceEncoder()

# --- Инициализация ---
# Создаем папку для профилей, если ее нет
os.makedirs(PROFILES_DIR, exist_ok=True)
print("Модуль идентификации готов.")


def _record_phrase(filename, duration=5):
    """Записывает аудио с микрофона в файл."""
    print(f"Запись фразы ({duration} сек)... Говорите!")
    audio_data = sd.rec(int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='int16')
    sd.wait()
    wavio.write(filename, audio_data, SAMPLE_RATE, sampwidth=2)
    print("Запись завершена.")


def create_profile():
    """Создает профиль нового водителя."""
    name = input("Введите имя нового водителя (латиницей, например, 'oleg'): ").lower()
    profile_path = os.path.join(PROFILES_DIR, f"{name}.json")

    if os.path.exists(profile_path):
        print(f"Профиль с именем '{name}' уже существует.")
        return

    print(f"\nСоздание профиля для '{name}'.")
    print("Сейчас вам нужно будет произнести несколько фраз для записи голоса.")

    temp_wav_path = os.path.join(PROFILES_DIR, "_temp_enroll.wav")
    _record_phrase(temp_wav_path, duration=10)  # Записываем длинную фразу для качества

    # Создаем голосовой отпечаток (эмбеддинг)
    wav = preprocess_wav(Path(temp_wav_path))
    embedding = ENCODER.embed_utterance(wav)

    # Создаем данные профиля
    profile_data = {
        "name": name,
        "voice_embedding": embedding.tolist(),  # Преобразуем в обычный список для JSON
        "preferences": {
            "default_temp": 21,
            "music_genre": "relax music"
        }
    }

    # Сохраняем в JSON-файл
    with open(profile_path, 'w', encoding='utf-8') as f:
        json.dump(profile_data, f, indent=4)

    os.remove(temp_wav_path)  # Удаляем временный аудиофайл
    print(f"\nПрофиль для '{name}' успешно создан!")


def identify_speaker():
    """Записывает голос и определяет, кто говорит."""
    print("\n--- Идентификация водителя ---")
    temp_wav_path = os.path.join(PROFILES_DIR, "_temp_identify.wav")
    _record_phrase(temp_wav_path, duration=5)

    # Загружаем все существующие профили
    known_embeddings = []
    profile_names = []
    for filename in os.listdir(PROFILES_DIR):
        if filename.endswith(".json"):
            with open(os.path.join(PROFILES_DIR, filename), 'r') as f:
                data = json.load(f)
                known_embeddings.append(np.array(data["voice_embedding"]))
                profile_names.append(data["name"])

    if not profile_names:
        print("Не найдено ни одного профиля. Сначала создайте профиль.")
        os.remove(temp_wav_path)
        return None

    # Создаем эмбеддинг для записанного голоса
    wav = preprocess_wav(Path(temp_wav_path))
    unknown_embedding = ENCODER.embed_utterance(wav)

    # Сравниваем новый голос со всеми в базе
    scores = [unknown_embedding @ known_emb for known_emb in known_embeddings]
    best_match_index = np.argmax(scores)

    # Порог схожести (можно подбирать)
    similarity_threshold = 0.75

    os.remove(temp_wav_path)

    if scores[best_match_index] > similarity_threshold:
        identified_name = profile_names[best_match_index]
        print(f"Распознан водитель: {identified_name.upper()} (Схожесть: {scores[best_match_index]:.2f})")

        # Загружаем полный профиль распознанного водителя
        profile_path = os.path.join(PROFILES_DIR, f"{identified_name}.json")
        with open(profile_path, 'r') as f:
            return json.load(f)
    else:
        print(f"Не удалось распознать водителя. (Макс. схожесть: {scores[best_match_index]:.2f})")
        return None