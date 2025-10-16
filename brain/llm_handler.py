# mrx_project/brain/llm_handler.py

import google.generativeai as genai
import json
# --- ИЗМЕНЕНИЕ: Возвращаемся к использованию простого config.py ---
import config

# --- Инициализация на уровне модуля ---

# 1. Конфигурируем API с ключом из вашего старого файла config.py
try:
    if not hasattr(config, 'GOOGLE_API_KEY') or not config.GOOGLE_API_KEY:
        raise AttributeError("API ключ GOOGLE_API_KEY не найден или пуст в файле config.py.")

    genai.configure(api_key=config.GOOGLE_API_KEY)
except AttributeError as e:
    print(f"ОШИБКА: {e}")
    print("Убедитесь, что у вас есть файл config.py с переменной GOOGLE_API_KEY = 'ваш_ключ'.")
    exit()

# 2. Глобальная переменная для хранения сессии чата.
chat_session = None


# --- Функции для управления мозгом ---

def reload_chat_session(system_prompt_text):
    """
    Полностью перезагружает сессию чата с новым системным промптом.
    """
    global chat_session
    print(f"--- Перезагрузка мозга с новым промптом... ---")

    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=system_prompt_text
        )
        chat_session = model.start_chat()
        print("Мозг успешно перезагружен.")
    except Exception as e:
        print(f"!!! КРИТИЧЕСКАЯ ОШИБКА при перезагрузке мозга: {e}")
        chat_session = None


def get_mrx_action(user_text):
    """
    СИНХРОННАЯ функция мозга. Для совместимости со старым main.py.
    """
    if not chat_session:
        print("!!! ОШИБКА: Мозг не инициализирован.")
        return {"command": "error", "response": "У меня проблемы с подключением к моему цифровому разуму."}

    response_obj = None
    try:
        print(f"-> Отправляю в мозг (sync): '{user_text}'")
        response_obj = chat_session.send_message(user_text)
        assistant_response_text = response_obj.text.strip().replace("```json", "").replace("```", "")
        action_data = json.loads(assistant_response_text)
        print(f"<- Мозг ответил (sync): {action_data}")
        return action_data
    except json.JSONDecodeError:
        print(f"!!! ОШИБКА JSON: Мозг вернул невалидный JSON: {response_obj.text if response_obj else 'No response'}")
        return {"command": "error", "response": "Что-то я сам себя не понял. Сформулируй иначе."}
    except Exception as e:
        print(f"!!! ОБЩАЯ ОШИБКА МОЗГА (sync): {e}")
        if response_obj and response_obj.prompt_feedback:
            print(f"!!! ОТВЕТ ЗАБЛОКИРОВАН: {response_obj.prompt_feedback}")
        return {"command": "error", "response": "Мой гугловский мозг сегодня барахлит."}


# --- НОВАЯ АСИНХРОННАЯ ФУНКЦИЯ ---
async def get_mrx_action_async(user_text):
    """
    АСИНХРОННАЯ версия для main_async.py.
    """
    if not chat_session:
        print("!!! ОШИБКА: Мозг не инициализирован.")
        return {"command": "error", "response": "У меня проблемы с подключением к моему цифровому разуму."}

    response_obj = None
    try:
        print(f"-> Отправляю в мозг (async): '{user_text}'")
        response_obj = await chat_session.send_message_async(user_text)
        assistant_response_text = response_obj.text.strip().replace("```json", "").replace("```", "")
        action_data = json.loads(assistant_response_text)
        print(f"<- Мозг ответил (async): {action_data}")
        return action_data
    except json.JSONDecodeError:
        print(f"!!! ОШИБКА JSON: Мозг вернул невалидный JSON: {response_obj.text if response_obj else 'No response'}")
        return {"command": "error", "response": "Что-то я сам себя не понял. Сформулируй иначе."}
    except Exception as e:
        print(f"!!! ОБЩАЯ ОШИБКА МОЗГА (async): {e}")
        if response_obj and hasattr(response_obj, 'prompt_feedback') and response_obj.prompt_feedback:
            print(f"!!! ОТВЕТ ЗАБЛОКИРОВАН: {response_obj.prompt_feedback}")
        return {"command": "error", "response": "Мой гугловский мозг сегодня барахлит."}