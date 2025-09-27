# voice/speaker_id.py (Версия со SpeechRecognition)

import speech_recognition as sr

def identify_speaker_by_codeword(wav_filepath, known_profiles):
    """
    Пытается распознать речь в файле и найти совпадение с кодовой фразой
    в профилях.
    """
    r = sr.Recognizer()
    with sr.AudioFile(wav_filepath) as source:
        audio = r.record(source) # читаем весь файл

    try:
        # Распознаем речь, используя быстрый офлайн-движок PocketSphinx
        recognized_text = r.recognize_sphinx(audio).lower()
        print(f"Распознана фраза для идентификации: '{recognized_text}'")

        for profile_name, profile_data in known_profiles.items():
            codeword = profile_data.get('codeword', '').lower()
            if codeword and codeword in recognized_text:
                print(f"Найдено совпадение с кодовым словом профиля '{profile_name}'")
                return profile_name

    except sr.UnknownValueError:
        print("Не удалось распознать речь для идентификации.")
    except sr.RequestError as e:
        print(f"Ошибка сервиса распознавания; {e}")

    return "unknown"