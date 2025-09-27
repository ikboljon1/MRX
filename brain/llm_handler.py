# mrx_project/brain/llm_handler.py

import google.generativeai as genai
import json
import config  # Импортируем наш файл с ключом
from brain.prompt import SYSTEM_PROMPT  # Импортируем наш промпт

# 1. Конфигурируем API с ключом из config.py
try:
    genai.configure(api_key=config.GOOGLE_API_KEY)
except AttributeError:
    print("ОШИБКА: API ключ не найден в config.py! Добавьте GOOGLE_API_KEY = 'ваш_ключ'.")
    exit()

# 2. Инициализируем модель
model = genai.GenerativeModel('gemini-2.5-flash')

# 3. Начинаем сессию чата, "скармливая" модели наш промпт
# Это гарантирует, что MRX будет помнить свою роль
chat_session = model.start_chat(history=[
    {
        "role": "user",
        "parts": [SYSTEM_PROMPT + "\n\nВодитель: Привет, MRX, системы в норме?"]
    },
    {
        "role": "model",
        "parts": ['{"command": "no_command", "response": "Привет, командир. Да, я в полном порядке. Готов к работе."}']
    }
])


def get_mrx_action(user_text):
    """
    Основная функция мозга. Принимает текст от пользователя,
    отправляет его в Gemini и возвращает результат в виде словаря.
    """
    response = None  # <--- ИЗМЕНЕНИЕ 1: Инициализируем переменную заранее
    try:
        response = chat_session.send_message(user_text)

        # Очищаем ответ от возможного "мусора" (```json ... ```)
        assistant_response_text = response.text.strip().replace("```json", "").replace("```", "")

        # Преобразуем текстовый JSON в Python-словарь
        action_data = json.loads(assistant_response_text)
        return action_data

    except Exception as e:
        print(f"!!! ОШИБКА МОЗГА: {e}")

        # <--- ИЗМЕНЕНИЕ 2: Теперь эта проверка безопасна.
        # Если 'response' не был создан, он будет None, и условие не выполнится.
        if response and response.prompt_feedback and hasattr(response.prompt_feedback, 'block_reason'):
            print(f"!!! ОТВЕТ ЗАБЛОКИРОВАН: {response.prompt_feedback.block_reason.name}")

        return {"command": "error", "response": "Мой гугловский мозг сегодня барахлит. Дай мне секунду."}