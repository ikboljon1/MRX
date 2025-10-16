# mrx_project/brain/llm_handler.py

import google.generativeai as genai
import json
import config

# --- Инициализация на уровне модуля ---
try:
    genai.configure(api_key=config.GOOGLE_API_KEY)
except AttributeError:
    print("ОШИБКА: API ключ GOOGLE_API_KEY не найден в файле config.py.")
    exit()

# --- Изменения: Вместо chat_session, теперь используем модель напрямую ---
model = None
system_prompt = ""
chat_history = []  # <--- НОВАЯ ГЛОБАЛЬНАЯ ПЕРЕМЕННАЯ ДЛЯ ИСТОРИИ


# --- Функции для управления мозгом ---

def reload_chat_session(system_prompt_text):
    """
    Перезагружает мозг с новым системным промптом и очищает историю.
    """
    global model, system_prompt, chat_history
    print(f"--- Перезагрузка мозга с новым промптом... ---")

    system_prompt = system_prompt_text
    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",  # Рекомендую 1.5-flash, он лучше держит контекст
            system_instruction=system_prompt
        )
        chat_history = []  # Очищаем историю при смене характера
        print("Мозг успешно перезагружен.")
    except Exception as e:
        print(f"!!! КРИТИЧЕСКАЯ ОШИБКА при перезагрузке мозга: {e}")
        model = None


# --- НОВАЯ АСИНХРОННАЯ ФУНКЦИЯ ---
async def get_mrx_action_async(user_text):
    """
    АСИНХРОННАЯ версия. Теперь с ЯВНОЙ передачей истории.
    """
    global chat_history
    if not model:
        print("!!! ОШИБКА: Мозг не инициализирован.")
        return {"command": "error", "response": "У меня проблемы с подключением к моему цифровому разуму."}

    response_obj = None
    try:
        print(f"-> Отправляю в мозг (контекст из {len(chat_history)} сообщений): '{user_text}'")

        # Создаем новую сессию чата КАЖДЫЙ РАЗ, но передаем ей СТАРУЮ историю
        chat_session = model.start_chat(history=chat_history)

        response_obj = await chat_session.send_message_async(user_text)

        # Обновляем нашу глобальную историю
        chat_history = chat_session.history

        # Ограничиваем историю, чтобы она не росла бесконечно (экономим токены)
        # Храним последние 10 сообщений (5 пар "вопрос-ответ")
        if len(chat_history) > 10:
            chat_history = chat_history[-10:]

        assistant_response_text = response_obj.text.strip().replace("```json", "").replace("```", "")
        action_data = json.loads(assistant_response_text)

        print(f"<- Мозг ответил (async): {action_data}")
        return action_data
    except json.JSONDecodeError:
        # Если LLM вернул не-JSON, значит он просто болтает.
        # Это может случиться, если он "забылся".
        # Мы не будем добавлять этот ответ в историю, чтобы не портить ее.
        bad_response_text = response_obj.text if response_obj else 'No response'
        print(f"!!! ОШИБКА JSON: Мозг вернул невалидный JSON: {bad_response_text}")
        return {"command": "error", "response": "Что-то я сам себя не понял. Сформулируй иначе."}
    except Exception as e:
        print(f"!!! ОБЩАЯ ОШИБКА МОЗГА (async): {e}")
        return {"command": "error", "response": "Мой гугловский мозг сегодня барахлит."}