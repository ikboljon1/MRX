# mrx_project/main.py

import time
from brain import llm_handler, prompt
from hardware import arduino_com, obd_manager
from voice import tts, stt
import language_manager

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

    # 2. Голосовое приветствие
    tts_model, tts_speaker, tts_lang, tts_sample_rate = language_manager.get_current_tts_params()
    tts.speak(tts_model, tts_speaker, tts_lang, language_manager.get_current_greeting(), tts_sample_rate)

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

            # --- ПРАВИЛЬНАЯ ПОСЛЕДОВАТЕЛЬНОСТЬ: РЕЧЬ -> ДЕЙСТВИЕ ---

            # 1. СНАЧАЛА MRX ГОВОРИТ
            tts.speak(tts_model, tts_speaker, tts_lang, response_text, tts_sample_rate)

            # 2. ПОТОМ ОТПРАВЛЯЕМ КОМАНДУ НА ARDUINO
            if command not in ['error', 'no_command', 'ask_clarification']:
                arduino_com.send_command(command)

            # Особая обработка для двухэтапной диагностики
            if command == 'run_diagnostics':
                diagnostics_report = obd_manager.run_full_diagnostics()
                report_for_llm = f"[РЕЗУЛЬТАТЫ ДИАГНОСТИКИ: {diagnostics_report}]"

                final_action = llm_handler.get_mrx_action(report_for_llm)
                final_response = final_action.get('response', 'Отчет готов.')

                # Озвучиваем отчет, а потом мигаем для подтверждения
                tts.speak(tts_model, tts_speaker, tts_lang, final_response, tts_sample_rate)
                arduino_com.send_command(command)

    except KeyboardInterrupt:
        print("\nПрограмма завершается.")
    finally:
        arduino_com.close()
        print("MRX отключен.")


if __name__ == "__main__":
    main()