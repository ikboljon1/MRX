# mrx_project/main.py

import time
import json
from brain import llm_handler, prompt, memory_manager, profile_manager
from hardware import arduino_com, obd_manager
from voice import tts, stt
import language_manager
from services import weather

# --- Константы для команд ---
SWITCH_TO_UZ_PHRASES = ["переключись на узбекский", "включи узбекский", "o'zbek tiliga o't"]
SWITCH_TO_RU_PHRASES = ["переключись на русский", "включи русский", "rus tiliga o't"]
EXIT_PHRASES = ["выход", "стоп", "хватит", "выйти", "отключайся", "chiqish"]


def main():
    """Главная функция программы."""
    # 1. Инициализация всех систем
    language_manager.init_language_system(llm_handler, prompt)
    obd_manager.initialize()
    arduino_com.initialize()
    profile_manager.load_driver_profile('guest')  # Загружаем профиль водителя "Гость" при старте

    # 2. Голосовое приветствие
    tts_model, tts_speaker, tts_lang, tts_sample_rate = language_manager.get_current_tts_params()
    tts.speak(tts_model, tts_speaker, tts_lang, language_manager.get_current_greeting(), tts_sample_rate)

    # 3. Проверка напоминаний при старте
    print("Проверка напоминаний на сегодня...")
    upcoming_notes = memory_manager.get_upcoming_notes()
    if upcoming_notes:
        notes_text = ", ".join([note['text'] for note in upcoming_notes])
        driver_name = profile_manager.get_current_driver_name()
        reminder = f"Кстати, {driver_name}, у тебя на сегодня есть заметки: {notes_text}."
        print(f"Найдено напоминание: {notes_text}")
        tts.speak(tts_model, tts_speaker, tts_lang, reminder, tts_sample_rate)

    try:
        # 4. Запуск основного цикла
        while True:
            # Слушаем команду от пользователя
            vosk_model = language_manager.get_current_stt_model()
            user_text = stt.listen(vosk_model)

            if not user_text:
                continue

            user_text_lower = user_text.lower()

            # Обработка системных команд (выход, смена языка)
            if any(phrase in user_text_lower for phrase in EXIT_PHRASES):
                tts.speak(tts_model, tts_speaker, tts_lang, "Понял. Отключаюсь.", tts_sample_rate)
                break

            switched = False
            if any(phrase in user_text_lower for phrase in SWITCH_TO_UZ_PHRASES):
                if language_manager.switch_language('uz', llm_handler, prompt):
                    tts_model, tts_speaker, tts_lang, tts_sample_rate = language_manager.get_current_tts_params()
                    tts.speak(tts_model, tts_speaker, tts_lang, language_manager.get_current_greeting(),
                              tts_sample_rate)
                    switched = True
            elif any(phrase in user_text_lower for phrase in SWITCH_TO_RU_PHRASES):
                if language_manager.switch_language('ru', llm_handler, prompt):
                    tts_model, tts_speaker, tts_lang, tts_sample_rate = language_manager.get_current_tts_params()
                    tts.speak(tts_model, tts_speaker, tts_lang, language_manager.get_current_greeting(),
                              tts_sample_rate)
                    switched = True
            if switched:
                continue

            # Формируем полный контекст для "мозга"
            car_state = obd_manager.get_car_state()
            errors_str = ', '.join(car_state.get('errors', [])) if car_state.get('errors') else 'нет'
            current_driver_profile = profile_manager.get_current_driver_data()
            profile_str = json.dumps(current_driver_profile, ensure_ascii=False) if current_driver_profile else '{}'

            context_for_llm = f"""
            [ТЕКУЩИЙ ПРОФИЛЬ ВОДИТЕЛЯ: {profile_str}]
            [ДАННЫЕ АВТОМОБИЛЯ:
            - Обороты: {car_state.get('rpm', 'N/A')} RPM
            - Скорость: {car_state.get('speed', 'N/A')} км/ч
            - Ошибки (DTC): {errors_str}
            ]
            [ЗАПРОС: {user_text}]"""

            action = llm_handler.get_mrx_action(context_for_llm)
            command = action.get('command', 'error')
            response_text = action.get('response', 'Что-то пошло не так...')

            is_internal_command = False  # Флаг для команд, не требующих отправки на Arduino

            # --- ОБРАБОТКА КОМАНД ПАМЯТИ ---
            if command.startswith("memory_add_note:"):
                is_internal_command = True
                try:
                    parts = command.split(":", 1)[1].split(';')
                    note_text = parts[0].strip()
                    due_date = parts[1].strip() if len(parts) > 1 and parts[1].strip() != 'null' else None
                    memory_manager.add_note(note_text, due_date)
                except Exception as e:
                    print(f"Ошибка разбора команды 'memory_add_note': {e}")
                    response_text = "Я не смог правильно разобрать команду для сохранения заметки."

            # --- ОБРАБОТКА КОМАНД ПРОФИЛЯ ВОДИТЕЛЯ ---
            if command.startswith("profile_"):
                is_internal_command = True
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
                            response_text = "Прости, я не могу изменять профиль Гостя. Давай создадим для тебя новый?"
                except Exception as e:
                    print(f"Ошибка обработки команды профиля водителя '{command}': {e}")
                    response_text = "Не смог выполнить команду, связанную с профилем водителя."

            # --- ОБРАБОТКА КОМАНД КОНТАКТОВ ---
            if command.startswith("contact_"):
                is_internal_command = True
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
                        contact_name = arg_part
                        tts.speak(tts_model, tts_speaker, tts_lang, response_text, tts_sample_rate)

                        contact_data = profile_manager.get_contact_info(contact_name)

                        feedback_for_llm = f"[ИНФОРМАЦИЯ О КОНТАКТЕ '{contact_name}': {json.dumps(contact_data, ensure_ascii=False) if contact_data else 'null'}]"
                        final_action = llm_handler.get_mrx_action(feedback_for_llm)
                        final_response = final_action.get('response', 'Не могу обработать информацию.')

                        tts.speak(tts_model, tts_speaker, tts_lang, final_response, tts_sample_rate)
                        continue  # Пропускаем остаток цикла

                except Exception as e:
                    print(f"Ошибка обработки команды контакта '{command}': {e}")
                    response_text = "Что-то пошло не так при работе с контактами."

            # --- ОБРАБОТКА КОМАНДЫ ПОГОДЫ ---
            if command.startswith("get_weather:"):
                tts.speak(tts_model, tts_speaker, tts_lang, response_text, tts_sample_rate)
                city = command.split(":", 1)[1].strip()
                weather_data = weather.get_weather(city)
                report_for_llm = f"[РЕЗУЛЬТАТ ЗАПРОСА ПОГОДЫ: {weather_data}]"
                final_action = llm_handler.get_mrx_action(report_for_llm)
                final_response = final_action.get('response', 'Не могу прочитать прогноз.')
                tts.speak(tts_model, tts_speaker, tts_lang, final_response, tts_sample_rate)
                continue

            # 1. СНАЧАЛА MRX ГОВОРИТ (если это не была двухэтапная команда)
            tts.speak(tts_model, tts_speaker, tts_lang, response_text, tts_sample_rate)

            # 2. ПОТОМ ОТПРАВЛЯЕМ КОМАНДУ НА ARDUINO
            # Мы не отправляем на Arduino внутренние команды
            if not is_internal_command and command not in ['error', 'no_command', 'ask_clarification']:
                arduino_com.send_command(command)

            # Особая обработка для двухэтапной диагностики
            if command == 'run_diagnostics':
                diagnostics_report = obd_manager.run_full_diagnostics()
                report_for_llm = f"[РЕЗУЛЬТАТЫ ДИАГНОСТИКИ: {diagnostics_report}]"
                final_action = llm_handler.get_mrx_action(report_for_llm)
                final_response = final_action.get('response', 'Отчет готов.')
                tts.speak(tts_model, tts_speaker, tts_lang, final_response, tts_sample_rate)

    except KeyboardInterrupt:
        print("\nПрограмма завершается.")
    finally:
        arduino_com.close()
        print("MRX отключен.")


if __name__ == "__main__":
    main()