# mrx_project/main.py

import time
import json
from brain import llm_handler, prompt, memory_manager, profile_manager, personality
from hardware import arduino_com, obd_manager
from voice import tts, stt, tts_voices, wake_word_detector
import language_manager
from services import weather

# --- СЛОВАРЬ ПРАВИЛЬНЫХ ПРОИЗНОШЕНИЙ ---
PRONUNCIATION_MAP = {
    "BMW E39": "Бэ-Эм-Вэ́ Е три́дцать де́вять", "BMW": "Бэ-Эм-Вэ́",
    "RPM": "оборо́тов", "DTC": "оши́бок"
}

# --- КОНСТАНТЫ ---
WAKE_WORDS = ["лиза", "лайза", "lisa"]
PROACTIVE_INTERVAL_SECONDS = 180
EXIT_PHRASES = ["выход", "стоп", "хватит", "выйти", "отключайся", "chiqish"]
SWITCH_TO_UZ_PHRASES = ["переключись на узбекский", "включи узбекский", "o'zbek tiliga o't"]
SWITCH_TO_RU_PHRASES = ["переключись на русский", "включи русский", "rus tiliga o't"]


def normalize_for_tts(text):
    """Готовит любой текст для идеального произношения."""
    if not isinstance(text, str): return ""
    for word, pronunciation in PRONUNCIATION_MAP.items():
        text = text.replace(word, pronunciation)
    return text


def main():
    """Главная функция программы."""
    # 1. === ИНИЦИАЛИЗАЦИЯ СИСТЕМ ===
    language_manager.init_language_system(llm_handler, prompt)
    llm_handler.reload_chat_session(prompt.PROMPTS_BY_CHARACTER['derzkiy'])
    obd_manager.initialize()
    arduino_com.initialize()
    profile_manager.load_driver_profile('guest')

    # --- Переменные состояния ассистента ---
    tts_model, tts_speaker, tts_lang, tts_sample_rate = language_manager.get_current_tts_params()
    current_character = 'derzkiy'
    current_speaker = tts_speaker
    assistant_mode = "talkative"
    last_proactive_check = time.time()

    # 2. === ПРИВЕТСТВИЕ И НАПОМИНАНИЯ ===
    driver_name = profile_manager.get_current_driver_name()
    greeting = personality.get_dynamic_greeting(driver_name)
    tts.speak(tts_model, current_speaker, tts_lang, normalize_for_tts(greeting), tts_sample_rate)

    upcoming_notes = memory_manager.get_upcoming_notes()
    if upcoming_notes:
        notes_text = ", ".join([note['text'] for note in upcoming_notes])
        reminder = f"Кстати, {driver_name}, у тебя на сегодня есть заметки: {notes_text}."
        tts.speak(tts_model, current_speaker, tts_lang, normalize_for_tts(reminder), tts_sample_rate)

    try:
        # 3. === ОСНОВНОЙ ЦИКЛ ПРОГРАММЫ ===
        while True:
            # --- ЭТАП 1: ПРОАКТИВНОЕ ПОВЕДЕНИЕ ---
            if assistant_mode == "talkative" and (time.time() - last_proactive_check) > PROACTIVE_INTERVAL_SECONDS:
                print("Проверка проактивных триггеров...")
                car_state = obd_manager.get_car_state()
                internal_prompt = None

                if car_state.get('speed', 1) < 5 and car_state.get('rpm', 0) > 600:
                    internal_prompt = "[ВНУТРЕННЕЕ СОБЫТИЕ: мы стоим на месте уже долгое время с заведенным двигателем.]"
                elif car_state.get('rpm', 0) > 4500:
                    internal_prompt = "[ВНУТРЕННЕЕ СОБЫТИЕ: высокие обороты двигателя, водитель ускоряется.]"

                if internal_prompt:
                    action = llm_handler.get_mrx_action(internal_prompt)
                    response = action.get('response')
                    tts.speak(tts_model, current_speaker, tts_lang, normalize_for_tts(response), tts_sample_rate)

                last_proactive_check = time.time()

            # --- ЭТАП 2: ОЖИДАНИЕ АКТИВАЦИОННОГО СЛОВА ---
            if not wake_word_detector.listen_for_wake_word(language_manager.get_current_stt_model(), WAKE_WORDS):
                continue

            # --- ЭТАП 3: АССИСТЕНТ ПРОСНУЛСЯ ---
            tts.speak(tts_model, current_speaker, tts_lang, normalize_for_tts("Слушаю"), tts_sample_rate)

            user_text = stt.listen(language_manager.get_current_stt_model(), listen_timeout=5.0)
            if not user_text:
                tts.speak(tts_model, current_speaker, tts_lang, normalize_for_tts("Не расслышала команду."),
                          tts_sample_rate)
                continue

            # --- ЭТАП 4: ОБРАБОТКА КОМАНДЫ ---
            user_text_lower = user_text.lower()

            if any(phrase in user_text_lower for phrase in EXIT_PHRASES):
                tts.speak(tts_model, current_speaker, tts_lang, "Поняла. Отключаюсь.", tts_sample_rate)
                break

            # --- Обработка смены языка ---
            switched = False
            if any(phrase in user_text_lower for phrase in SWITCH_TO_UZ_PHRASES):
                if language_manager.switch_language('uz', llm_handler, prompt):
                    tts_model, tts_speaker, tts_lang, tts_sample_rate = language_manager.get_current_tts_params()
                    greeting_after_switch = personality.get_dynamic_greeting(driver_name)
                    tts.speak(tts_model, current_speaker, tts_lang, normalize_for_tts(greeting_after_switch),
                              tts_sample_rate)
                    switched = True
            elif any(phrase in user_text_lower for phrase in SWITCH_TO_RU_PHRASES):
                if language_manager.switch_language('ru', llm_handler, prompt):
                    tts_model, tts_speaker, tts_lang, tts_sample_rate = language_manager.get_current_tts_params()
                    greeting_after_switch = personality.get_dynamic_greeting(driver_name)
                    tts.speak(tts_model, current_speaker, tts_lang, normalize_for_tts(greeting_after_switch),
                              tts_sample_rate)
                    switched = True
            if switched: continue

            # --- Получение ответа от LLM ---
            car_state = obd_manager.get_car_state()
            context_for_llm = f"""[ДАННЫЕ АВТО: Обороты: {car_state.get('rpm', 'N/A')} RPM] [ЗАПРОС: {user_text}]"""
            action = llm_handler.get_mrx_action(context_for_llm)
            command = action.get('command', 'error')
            response_text = action.get('response', 'Что-то пошло не так...')

            # --- Обработка команд, меняющих состояние ассистента ---
            if command.startswith("set_character:"):
                new_character = command.split(":", 1)[1].strip()
                if new_character in prompt.PROMPTS_BY_CHARACTER:
                    current_character = new_character
                    llm_handler.reload_chat_session(prompt.PROMPTS_BY_CHARACTER[current_character])
                    print(f"--- Характер изменен на: {current_character} ---")
                else:
                    response_text = "Простите, но такой личности в моей прошивке не нашлось."
                tts.speak(tts_model, current_speaker, tts_lang, normalize_for_tts(response_text), tts_sample_rate)
                continue

            if command.startswith("set_voice:"):
                new_speaker = command.split(":", 1)[1].strip()
                if new_speaker in tts_voices.get_valid_speakers():
                    current_speaker = new_speaker
                    print(f"--- Голос изменен на: {current_speaker} ---")
                else:
                    response_text = "Такого голоса в моих настройках нет."
                tts.speak(tts_model, current_speaker, tts_lang, normalize_for_tts(response_text), tts_sample_rate)
                continue

            if command.startswith("set_mode:"):
                new_mode = command.split(":", 1)[1].strip()
                if new_mode in ["talkative", "quiet"]:
                    assistant_mode = new_mode
                    print(f"--- Режим изменен на: {assistant_mode} ---")
                tts.speak(tts_model, current_speaker, tts_lang, normalize_for_tts(response_text), tts_sample_rate)
                continue

            # --- ОБРАБОТКА ФУНКЦИОНАЛЬНЫХ КОМАНД ---
            if command.startswith("memory_add_note:"):
                try:
                    parts = command.split(":", 1)[1].split(';')
                    note_text = parts[0].strip()
                    due_date = parts[1].strip() if len(parts) > 1 and parts[1].strip() != 'null' else None
                    memory_manager.add_note(note_text, due_date)
                except Exception as e:
                    print(f"Ошибка разбора команды 'memory_add_note': {e}")
                    response_text = "Я не смог правильно разобрать команду для сохранения заметки."

            elif command.startswith("profile_"):
                try:
                    cmd_part, arg_part = command.split(":", 1) if ":" in command else (command, None)
                    if arg_part: arg_part = arg_part.strip()
                    if cmd_part == "profile_switch":
                        profile_manager.load_driver_profile(arg_part)
                    elif cmd_part == "profile_create":
                        profile_manager.create_driver_profile(arg_part)
                    elif cmd_part == "profile_update":
                        key, value = [x.strip() for x in arg_part.split(';', 1)]
                        if not profile_manager.update_current_driver_profile(key, value):
                            response_text = "Прости, профиль Гостя менять нельзя. Давай создадим для тебя новый?"
                except Exception as e:
                    print(f"Ошибка обработки команды профиля водителя '{command}': {e}")
                    response_text = "Не смог выполнить команду, связанную с профилем."

            elif command.startswith("contact_"):
                try:
                    cmd_part, arg_part = command.split(":", 1)
                    arg_part = arg_part.strip()
                    if cmd_part == "contact_add":
                        if profile_manager.contact_exists(arg_part):
                            response_text = f"Контакт с именем {arg_part} уже есть."
                        else:
                            profile_manager.create_contact(arg_part)
                    elif cmd_part == "contact_update":
                        name, key_value_part = [x.strip() for x in arg_part.split(';', 1)]
                        key, value = [x.strip() for x in key_value_part.split(';', 1)]
                        if not profile_manager.update_contact_info(name, key, value):
                            response_text = f"Не нашла контакта по имени {name}, чтобы обновить информацию."
                    elif cmd_part == "contact_get_info":
                        tts.speak(tts_model, current_speaker, tts_lang, normalize_for_tts(response_text),
                                  tts_sample_rate)
                        contact_data = profile_manager.get_contact_info(arg_part)
                        feedback = f"[ИНФОРМАЦИЯ О КОНТАКТЕ '{arg_part}': {json.dumps(contact_data, ensure_ascii=False) if contact_data else 'null'}]"
                        final_action = llm_handler.get_mrx_action(feedback)
                        final_response = final_action.get('response', 'Не могу обработать информацию.')
                        tts.speak(tts_model, current_speaker, tts_lang, normalize_for_tts(final_response),
                                  tts_sample_rate)
                        continue
                except Exception as e:
                    print(f"Ошибка обработки команды контакта '{command}': {e}")
                    response_text = "Что-то пошло не так при работе с контактами."

            elif command.startswith("get_weather:"):
                tts.speak(tts_model, current_speaker, tts_lang, normalize_for_tts(response_text), tts_sample_rate)
                city = command.split(":", 1)[1].strip()
                weather_data = weather.get_weather(city)
                report = f"[РЕЗУЛЬТАТ ЗАПРОСА ПОГОДЫ: {weather_data}]"
                final_action = llm_handler.get_mrx_action(report)
                final_response = final_action.get('response', 'Не могу прочитать прогноз.')
                tts.speak(tts_model, current_speaker, tts_lang, normalize_for_tts(final_response), tts_sample_rate)
                continue

            # --- ОЗВУЧКА И ОТПРАВКА КОМАНДЫ НА ЖЕЛЕЗО ---
            is_internal_command = command.startswith(('memory', 'profile', 'contact')) or command in ['error',
                                                                                                      'no_command',
                                                                                                      'ask_clarification',
                                                                                                      'set_voice',
                                                                                                      'set_mode',
                                                                                                      'set_character']

            if not command.startswith(('contact_get_info', 'get_weather')):
                tts.speak(tts_model, current_speaker, tts_lang, normalize_for_tts(response_text), tts_sample_rate)

            if not is_internal_command:
                arduino_com.send_command(command)

            if command == 'run_diagnostics':
                diagnostics_report = obd_manager.run_full_diagnostics()
                report_for_llm = f"[РЕЗУЛЬТАТЫ ДИАГНОСТИКИ: {diagnostics_report}]"
                final_action = llm_handler.get_mrx_action(report_for_llm)
                final_response = final_action.get('response', 'Отчет готов.')
                tts.speak(tts_model, current_speaker, tts_lang, normalize_for_tts(final_response), tts_sample_rate)

    except KeyboardInterrupt:
        print("\nПрограмма завершается.")
    finally:
        arduino_com.close()
        print("MRX отключен.")


if __name__ == "__main__":
    main()