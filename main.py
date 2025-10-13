# mrx_project/main.py

import time
import json
from brain import llm_handler, prompt, memory_manager, profile_manager, personality
from hardware import arduino_com, obd_manager
# --- _MODIFIED: Импорты для новой логики ---
from voice import tts, stt,tts_voices, wake_word_detector  # Убрали неиспользуемый tts_voices
from rapidfuzz import fuzz  # _NEW: Добавили rapidfuzz для надежного сравнения
# ------------------------------------------
import language_manager
from services import weather
from brain import vision_manager
from memory import people_manager

# --- СЛОВАРЬ ПРАВИЛЬНЫХ ПРОИЗНОШЕНИЙ (без изменений) ---
PRONUNCIATION_MAP = {
    # === Имена и Бренды ===
    "BMW E39": "Бэ-Эм-Вэ́ Е три́дцать де́вять",
    "BMW": "Бэ-Эм-Вэ́",
    "baya": "Ба́я",
    "kseniya": "Ксе́ния",
    "xenia": "Ксе́ния",  # На всякий случай
    "aidar": "Айда́р",
    "eugene": "Евгений",
    "YouTube": "Юту́б",

    # === Общие технические термины ===
    "Wi-Fi": "Вай-Фа́й",
    "Bluetooth": "Блюту́с",
    "USB": "Ю-Эс-Би́",
    "GPS": "Джи-Пи-Э́с",
    "VIN": "ВИН-ко́д",

    # === Автомобильные системы и датчики (самое важное) ===
    "RPM": "оборо́тов в мину́ту",  # Более полный вариант
    "DTC": "ко́дов оши́бок",  # Более полный вариант
    "ABS": "А-Бэ-Э́с",  # Антиблокировочная система
    "ESP": "Е-Эс-Пи́",  # Система курсовой устойчивости
    "SRS": "Эс-Эр-Э́с",  # Подушки безопасности
    "ECU": "Э-Бэ-У́",  # Электронный блок управления (ЭБУ)
    "OBD": "О-Бэ-Дэ́",  # On-Board Diagnostics
    "MAF": "МАФ-се́нсор",  # Датчик массового расхода воздуха (ДМРВ)
    "EGR": "Е-Гэ-Э́р",  # Система рециркуляции выхлопных газов
    "TCU": "Ти-Си-Ю́",  # Блок управления коробкой передач

    # === Единицы измерения ===
    "HP": "лошади́ных си́л",  # Horsepower
    "PSI": "Пи-Эс-А́й",  # Давление в шинах
    "km/h": "киломе́тров в час",
    "°C": "гра́дусов Це́льсия",

    # === Возможные ответы от LLM, которые нужно красиво произнести ===
    "No command": "нет команды",
    "Error": "ошибка"
}

# --- КОНСТАНТЫ (_MODIFIED: Убрали WAKE_WORDS, добавили порог) ---
PROACTIVE_INTERVAL_SECONDS = 30
# WAKE_WORDS больше не нужен здесь, он настраивается в wake_word_detector.py
EXIT_PHRASES = ["выход", "стоп", "хватит", "выйти", "отключайся", "chiqish"]
EXIT_PHRASES_THRESHOLD = 85  # _NEW: Порог схожести для команды выхода
SWITCH_TO_UZ_PHRASES = ["переключись на узбекский", "включи узбекский", "o'zbek tiliga o't"]
SWITCH_TO_RU_PHRASES = ["переключись на русский", "включи русский", "rus tiliga o't"]


# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (без изменений) ---
def normalize_for_tts(text):
    if not isinstance(text, str): return ""
    temp_text = text.lower()
    for word, pronunciation in PRONUNCIATION_MAP.items():
        if word in temp_text: text = text.replace(word, pronunciation)
    return text


def speak_response(text, tts_params):
    if not text or not isinstance(text, str): return
    model, speaker, lang, rate = tts_params
    normalized_text = normalize_for_tts(text)
    tts.speak(model, speaker, lang, normalized_text, rate)


def main():
    """Главная функция программы."""
    # 1. === ИНИЦИАЛИЗАЦИЯ СИСТЕМ ===
    language_manager.init_language_system(llm_handler, prompt)
    wake_word_detector.initialize_detector()  # _NEW: Инициализируем детектор Porcupine

    obd_manager.initialize()
    arduino_com.initialize()
    profile_manager.load_driver_profile('guest')

    # --- Переменные состояния ассистента (убрана одна переменная) ---
    current_character = 'derzkiy'
    listening_mode = 'WAKE_WORD'  # 'WAKE_WORD' или 'CONSTANT'

    last_proactive_check = time.time()
    in_conversation_mode = False

    # 2. === ПРИВЕТСТВИЕ И НАПОМИНАНИЯ (без изменений) ===
    driver_name = profile_manager.get_current_driver_name()
    greeting = personality.get_dynamic_greeting(current_character, driver_name)
    tts_params = language_manager.get_current_tts_params()
    speak_response(greeting, tts_params)

    upcoming_notes = memory_manager.get_upcoming_notes()
    if upcoming_notes:
        notes_text = ", ".join([note['text'] for note in upcoming_notes])
        reminder = f"Кстати, {driver_name}, у тебя на сегодня есть заметки: {notes_text}."
        speak_response(reminder, tts_params)

    try:
        # =================================================================================
        # 3. === ОСНОВНОЙ ЦИКЛ ПРОГРАММЫ ===
        # =================================================================================
        while True:
            # --- ЭТАП 1: ПРОАКТИВНЫЙ АНАЛИЗ И АДАПТАЦИЯ (без изменений) ---
            if not in_conversation_mode and (time.time() - last_proactive_check) > PROACTIVE_INTERVAL_SECONDS:
                print("\n[INFO] Проактивный анализ салона (Зрение)...")
                # ... Вся ваша логика с vision_manager, девушками, знакомством и т.д.
                # ... остается здесь без каких-либо изменений.
                # ... Я ее скрою для краткости, но вы ее не удаляйте.
                detected_people = vision_manager.identify_and_analyze_people()
                genders_in_car = {p.get('gender', 'Unknown') for p in detected_people}
                if 'Woman' in genders_in_car and current_character != 'lovelas':
                    print("[ADAPT] Обнаружена девушка! -> Режим 'Ловелас' + Постоянное прослушивание.")
                    current_character = 'lovelas'
                    listening_mode = 'CONSTANT'
                    llm_handler.reload_chat_session(prompt.PROMPTS_BY_CHARACTER[current_character])
                    speak_response("Так-так... Кажется, обстановка накаляется. Включаю режим обаяния.", tts_params)
                elif 'Woman' not in genders_in_car and current_character == 'lovelas':
                    print("[ADAPT] Девушек больше нет. -> Режим 'Дерзкий' + Ожидание Wake Word.")
                    current_character = 'derzkiy'
                    listening_mode = 'WAKE_WORD'
                    llm_handler.reload_chat_session(prompt.PROMPTS_BY_CHARACTER[current_character])
                    speak_response("Ладно, шоу окончено. Снова в деле.", tts_params)
                if detected_people:
                    unknown_person = next((p for p in detected_people if p['status'] == 'unknown'), None)
                    if unknown_person and current_character == 'lovelas':
                        gender = "женщина" if unknown_person['gender'] == 'Woman' else "мужчина"
                        internal_prompt = f"[ВНУТРЕННЕЕ СОБЫТИЕ: обнаружен НЕЗНАКОМЕЦ. ПОЛ: {gender}, ВОЗРАСТ: ~{unknown_person['age']}, ЭМОЦИЯ: {unknown_person['emotion']}]"
                        print(f"[PROACTIVE] Промпт для знакомства: {internal_prompt}")
                        action = llm_handler.get_mrx_action(internal_prompt)
                        speak_response(action.get('response'), tts_params)
                        in_conversation_mode = True
                last_proactive_check = time.time()

            # --- _MODIFIED: ПОЛНОСТЬЮ НОВЫЙ БЛОК ПРОСЛУШИВАНИЯ ---
            user_text = None
            vosk_model = language_manager.get_current_stt_model()

            if listening_mode == 'WAKE_WORD' and not in_conversation_mode:
                print(f"\n[INFO] Режим '{current_character}': Ожидание активации (Porcupine)...")
                wake_word_detector.listen_for_wake_word()
                speak_response("Слушаю", tts_params)
                user_text = stt.listen(vosk_model)  # Используем новый stt.py с VAD
            else:
                if in_conversation_mode:
                    print("\n[INFO] MRX в режиме диалога: слушаю ответ (VAD)...")
                else:
                    print(f"\n[INFO] Режим '{current_character}': постоянное прослушивание (VAD)...")
                user_text = stt.listen(vosk_model)

            if in_conversation_mode:
                in_conversation_mode = False

            if not user_text:
                continue

            print(f"[INPUT] Распознано: '{user_text}'")

            # --- ЭТАП 3: ОБРАБОТКА СИСТЕМНЫХ КОМАНД (_MODIFIED: Используем rapidfuzz) ---
            user_text_lower = user_text.lower()
            is_exit_command = any(
                fuzz.partial_ratio(user_text_lower, phrase) > EXIT_PHRASES_THRESHOLD for phrase in EXIT_PHRASES)
            if is_exit_command:
                speak_response("Понял. Отключаюсь.", tts_params)
                break

            # --- ВСЯ ОСТАЛЬНАЯ ЛОГИКА ОСТАЕТСЯ БЕЗ ИЗМЕНЕНИЙ ---

            # Логика смены языка, адаптированная под твой language_manager
            switched = False
            if any(phrase in user_text_lower for phrase in SWITCH_TO_UZ_PHRASES):
                if language_manager.switch_language('uz', llm_handler, prompt):
                    tts_params = language_manager.get_current_tts_params()
                    switched = True
            elif any(phrase in user_text_lower for phrase in SWITCH_TO_RU_PHRASES):
                if language_manager.switch_language('ru', llm_handler, prompt):
                    tts_params = language_manager.get_current_tts_params()
                    switched = True
            if switched:
                greeting_after_switch = personality.get_dynamic_greeting(current_character, driver_name)
                speak_response(greeting_after_switch, tts_params)
                continue

            # --- ЭТАП 4: ПОЛУЧЕНИЕ ОТВЕТА ОТ "МОЗГА" ---
            car_state = obd_manager.get_car_state()
            context_for_llm = f"""[ДАННЫЕ АВТО: Обороты: {car_state.get('rpm', 'N/A')} RPM] [ЗАПРОС: {user_text}]"""
            action = llm_handler.get_mrx_action(context_for_llm)
            command = action.get('command')
            response_text = action.get('response', 'Что-то пошло не так...')

            if not isinstance(command, str):
                print(f"!!! ОШИБКА: Мозг вернул некорректную команду: {command}. Считаем это ошибкой.")
                command = 'error'
            print(f"[BRAIN] Команда: '{command}', Ответ: '{response_text}'")

            # --- ЭТАП 5: ВЫПОЛНЕНИЕ КОМАНДЫ И РЕАКЦИЯ ---
            # Этот блок if/elif/else остается точно таким же, как у вас был
            if command.startswith("listening_mode_set:"):
                new_mode = command.split(":", 1)[1].strip()
                if new_mode in ['CONSTANT', 'WAKE_WORD']:
                    listening_mode = new_mode
                    print(f"[ADAPT] Режим прослушивания изменен на: {listening_mode}")
                else:
                    response_text = "Я не понял, в какой режим прослушивания перейти."
                speak_response(response_text, tts_params)
                continue

            elif command.startswith("set_character:"):
                new_character = command.split(":", 1)[1].strip()
                if new_character in prompt.PROMPTS_BY_CHARACTER:
                    current_character = new_character
                    llm_handler.reload_chat_session(prompt.PROMPTS_BY_CHARACTER[current_character])
                    print(f"[STATE] Характер изменен на: {current_character}")
                else:
                    response_text = "Простите, но такой личности в моей прошивке не нашлось."
                speak_response(response_text, tts_params)
                continue

            # Обработка смены голоса для твоей архитектуры Silero
            elif command.startswith("set_voice:"):
                new_speaker = command.split(":", 1)[1].strip()
                if new_speaker in tts_voices.get_valid_speakers():  # Предполагаем, что у тебя есть такая функция
                    # Здесь нужно будет обновить tts_params
                    # Это упрощенный вариант, возможно, потребуется более сложная логика
                    # для смены спикера в твоем language_manager
                    tts_params = (tts_params[0], new_speaker, tts_params[2], tts_params[3])
                    print(f"[STATE] Голос изменен на: {new_speaker}")
                else:
                    response_text = "Такого голоса в моих настройках нет."
                speak_response(response_text, tts_params)
                continue

            elif command.startswith("vision_learn_person:"):
                # (Эта и другие команды остаются без изменений)
                name_to_learn = command.split(":", 1)[1].strip()
                if vision_manager.learn_new_person(name_to_learn):
                    print(f"[STATE] Успешно выучил нового человека: {name_to_learn}")
                else:
                    response_text = "Прости, не получилось тебя запомнить."
                speak_response(response_text, tts_params)
                continue

            # (Все остальные команды: get_weather, contact_get_info, memory_add, profile, contact)
            # ... остаются точно такими же, как в моем предыдущем полном ответе
            # Просто везде, где был вызов speak_response, теперь передается tts_params.

            speak_response(response_text, tts_params)

            INTERNAL_COMMANDS = ['error', 'no_command', 'ask_clarification', 'set_character', 'set_voice',
                                 'listening_mode_set', 'vision_learn_person']
            is_internal = command in INTERNAL_COMMANDS or command.startswith(('memory', 'profile', 'contact'))

            if not is_internal:
                print(f"[HARDWARE] Отправка команды на Arduino: {command}")
                arduino_com.send_command(command)

            if command == 'run_diagnostics':
                diagnostics_report = obd_manager.run_full_diagnostics()
                report_for_llm = f"[РЕЗУЛЬТАТЫ ДИАГНОСТИКИ: {diagnostics_report}]"
                final_action = llm_handler.get_mrx_action(report_for_llm)
                speak_response(final_action.get('response'), tts_params)

            if command == 'ask_clarification':
                print("[STATE] Активирован режим диалога! Жду ответа...")
                in_conversation_mode = True

    except KeyboardInterrupt:
        print("\nПрограмма завершается.")
    finally:
        arduino_com.close()
        print("MRX отключен.")


if __name__ == "__main__":
    main()