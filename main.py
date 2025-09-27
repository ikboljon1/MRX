# mrx_project/main.py (Версия с голосом)

from brain import llm_handler
from hardware import arduino_com
from voice import tts, stt  # <-- Импортируем наши новые модули


def main():
    """
    Главная функция программы. Запускает основной цикл.
    """
    # Приветственное сообщение голосом
    tts.speak("Лиза на связи. Готов к работе.")

    while True:
        # 1. Слушаем команду от пользователя
        user_text = stt.listen()

        # Проверяем, не сказал ли пользователь "выход" или "стоп"
        if user_text.lower() in ["выход", "стоп", "хватит", "выйти"]:
            tts.speak("Понял. Отключаюсь.")
            break

        if not user_text:  # Если ничего не распозналось, слушаем снова
            continue

        # 2. Отправляем текст в "мозг" и получаем решение
        action = llm_handler.get_mrx_action(user_text)

        command = action.get('command', 'error')
        response_text = action.get('response', 'Что-то пошло не так...')

        # 3. "Говорим" ответ MRX голосом
        tts.speak(response_text)

        # 4. Отправляем команду на "железо" (через нашу заглушку)
        arduino_com.send_command(command)


if __name__ == "__main__":
    main()