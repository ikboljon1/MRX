# mrx_project/main.py

import time
from brain import llm_handler, prompt, memory_manager  # <-- Добавляем импорт memory_manager
from hardware import arduino_com, obd_manager
from voice import tts, stt
import language_manager
from services import weather

# --- Константы для команд (без изменений) ---
SWITCH_TO_UZ_PHRASES = ["переключись на узбекский", "включи узбекский", "o'zbek tiliga o't"]
SWITCH_TO_RU_PHRASES = ["переключись на русский", "включи русский", "rus tiliga o't"]
EXIT_PHRASES = ["выход", "стоп", "хватит", "выйти", "отключайся", "chiqish"]


def main():
    """Главная функция программы."""
    # 1. Инициализация всех систем
    language_manager.init_language_system(llm_handler, prompt)
    obd_manager.initialize()
    arduino_com.initialize()

    # 2. Голосовое приветствие
    tts_model, tts_speaker, tts_lang, tts_sample_rate = language_manager.get_current_tts_params()
    tts.speak(tts_model, tts_speaker, tts_lang, language_manager.get_current_greeting(), tts_sample_rate)

    # --- НОВЫЙ БЛОК: ПРОВЕРКА НАПОМИНАНИЙ ПРИ СТАРТЕ ---
    print("Проверка напоминаний на сегодня...")
    upcoming_notes = memory_manager.get_upcoming_notes()
    if upcoming_notes:
        notes_text = ", ".join([note['text'] for note in upcoming_notes])
        # TODO: Заменить 'водитель' на имя из профиля, когда профили будут готовы
        reminder = f"Кстати, водитель, у тебя на сегодня есть заметки: {notes_text}."
        print(f"Найдено напоминание: {notes_text}")
        tts.speak(tts_model, tts_speaker, tts_lang, reminder, tts_sample_rate)

    try:
        # 3. Запуск основного цикла
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

            # ... (логика смены языка остается без изменений) ...
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
            context_for_llm = f"""
            [ДАННЫЕ АВТОМОБИЛЯ:
            - Обороты: {car_state.get('rpm', 'N/A')} RPM
            - Скорость: {car_state.get('speed', 'N/A')} км/ч
            - Температура ОЖ: {car_state.get('coolant_temp', 'N/A')} °C
            - Ошибки (DTC): {errors_str}
            ]
            [ЗАПРОС ВОДИТЕЛЯ: {user_text}]"""

            action = llm_handler.get_mrx_action(context_for_llm)
            command = action.get('command', 'error')
            response_text = action.get('response', 'Что-то пошло не так...')

            # --- НОВЫЙ БЛОК: ОБРАБОТКА КОМАНД ПАМЯТИ ---
            is_memory_command = False
            if command.startswith("memory_add_note:"):
                try:
                    parts = command.split(":", 1)[1].split(';')
                    note_text = parts[0].strip()
                    # Проверяем, есть ли дата и не является ли она 'null'
                    due_date = parts[1].strip() if len(parts) > 1 and parts[1].strip() != 'null' else None
                    memory_manager.add_note(note_text, due_date)
                    is_memory_command = True
                except IndexError:
                    print("Ошибка разбора команды 'memory_add_note'. Неверный формат.")
                    response_text = "Я не смог правильно разобрать команду для сохранения заметки."
            # --- КОНЕЦ БЛОКА ПАМЯТИ ---

            # --- НОВЫЙ БЛОК: ОБРАБОТКА КОМАНДЫ ПОГОДЫ (ДВУХЭТАПНЫЙ ДИАЛОГ) ---
            if command.startswith("get_weather:"):
                # 1. Сначала озвучиваем, что начинаем процесс
                tts.speak(tts_model, tts_speaker, tts_lang, response_text, tts_sample_rate)

                # 2. Извлекаем название города и делаем запрос в интернет
                city = command.split(":", 1)[1].strip()
                weather_data = weather.get_weather(city)

                # 3. Формируем новый запрос для LLM, но уже с результатами
                report_for_llm = f"[РЕЗУЛЬТАТ ЗАПРОСА ПОГОДЫ: {weather_data}]"

                print(
                    f"\n--- Отправка данных о погоде в мозг для анализа ---\n{report_for_llm}\n------------------------------------------------\n")

                # 4. Просим LLM "человеческим языком" озвучить результат
                final_action = llm_handler.get_mrx_action(report_for_llm)
                final_response = final_action.get('response', 'Не могу прочитать прогноз.')

                # 5. Озвучиваем финальный, осмысленный отчет
                tts.speak(tts_model, tts_speaker, tts_lang, final_response, tts_sample_rate)

                # Пропускаем остаток цикла, т.к. диалог о погоде завершен
                continue
             # --- КОНЕЦ БЛОКА ПОГОДЫ ---

            # 1. СНАЧАЛА MRX ГОВОРИТ
            tts.speak(tts_model, tts_speaker, tts_lang, response_text, tts_sample_rate)

            # 2. ПОТОМ ОТПРАВЛЯЕМ КОМАНДУ НА ARDUINO
            # Мы не отправляем на Arduino команды памяти и другие "виртуальные" команды
            if not is_memory_command and command not in ['error', 'no_command', 'ask_clarification']:
                arduino_com.send_command(command)

            # Особая обработка для двухэтапной диагностики
            if command == 'run_diagnostics':
                diagnostics_report = obd_manager.run_full_diagnostics()
                report_for_llm = f"[РЕЗУЛЬТАТЫ ДИАГНОСТИКИ: {diagnostics_report}]"

                final_action = llm_handler.get_mrx_action(report_for_llm)
                final_response = final_action.get('response', 'Отчет готов.')

                tts.speak(tts_model, tts_speaker, tts_lang, final_response, tts_sample_rate)
                arduino_com.send_command(command)

    except KeyboardInterrupt:
        print("\nПрограмма завершается.")
    finally:
        arduino_com.close()
        print("MRX отключен.")


if __name__ == "__main__":
    main()