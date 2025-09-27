# mrx_project/brain/llm_handler.py

import google.generativeai as genai
import json
import config

# --- Инициализация на уровне модуля (выполняется один раз) ---

# 1. Конфигурируем API с ключом из config.py
try:
    genai.configure(api_key=config.GOOGLE_API_KEY)
except AttributeError:
    print("ОШИБКА: API ключ не найден в config.py! Добавьте GOOGLE_API_KEY = 'ваш_ключ'.")
    exit()

# 2. Глобальная переменная для хранения сессии чата. Изначально пустая.
#    Именно она хранит "состояние" и "память" диалога.
chat_session = None

# --- Функции для управления мозгом ---

# ПЕРЕИМЕНУЙТЕ ВАШУ ФУНКЦИЮ ИМЕННО ТАК
def reload_chat_session(system_prompt_text):
    """
    Полностью перезагружает сессию чата с новым системным промптом.
    """
    global chat_session
    print(f"--- Перезагрузка мозга с новым промптом... ---")

    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=system_prompt_text # Используем переданный промпт
        )
        chat_session = model.start_chat()
        print("Мозг успешно перезагружен.")
    except Exception as e:
        print(f"!!! КРИТИЧЕСКАЯ ОШИБКА при перезагрузке мозга: {e}")
        chat_session = None


def get_mrx_action(user_text):
    """
    Основная функция мозга. Принимает текст от пользователя,
    отправляет его в текущую сессию чата и возвращает результат.
    """
    # Проверка, был ли мозг успешно инициализирован
    if not chat_session:
        print("!!! ОШИБКА: Мозг не инициализирован. Вызовите reload_brain() сначала.")
        return {"command": "error", "response": "У меня проблемы с подключением к моему цифровому разуму. Попробуй позже."}

    response_obj = None
    try:
        print(f"-> Отправляю в мозг: '{user_text}'")
        response_obj = chat_session.send_message(user_text)

        # Очищаем ответ от возможного "мусора" (```json ... ```)
        assistant_response_text = response_obj.text.strip().replace("```json", "").replace("```", "")

        # Преобразуем текстовый JSON в Python-словарь
        action_data = json.loads(assistant_response_text)
        print(f"<- Мозг ответил: {action_data}")
        return action_data

    except json.JSONDecodeError:
        print(f"!!! ОШИБКА JSON: Мозг вернул невалидный JSON: {response_obj.text if response_obj else 'No response'}")
        return {"command": "error", "response": "Что-то я сам себя не понял. Сформулируй иначе."}
    except Exception as e:
        print(f"!!! ОБЩАЯ ОШИБКА МОЗГА: {e}")
        if response_obj and response_obj.prompt_feedback:
             print(f"!!! ОТВЕТ ЗАБЛОКИРОВАН: {response_obj.prompt_feedback}")
        return {"command": "error", "response": "Мой гугловский мозг сегодня барахлит. Дай мне секунду."}