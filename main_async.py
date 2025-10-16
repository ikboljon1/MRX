# mrx_project/main_async.py

import asyncio
import functools
import time
import json

import sfx_player
from brain import llm_handler, prompt, memory_manager, profile_manager, personality, offline_handler
from hardware import arduino_com, obd_manager
from voice import tts, stt, tts_voices, wake_word_detector
from rapidfuzz import fuzz
import language_manager
from services import weather, network_manager, media_player  # <-- ДОБАВЛЕН media_player
from brain import vision_manager
from memory import people_manager
import multiprocessing as mp
from brain import vision_worker
import queue



# --- КОНСТАНТЫ ---
PROACTIVE_INTERVAL_SECONDS = 120
EXIT_PHRASES = ["выход", "стоп", "хватит", "выйти", "отключайся", "chiqish"]
EXIT_PHRASES_THRESHOLD = 85
SWITCH_TO_UZ_PHRASES = ["переключись на узбекский", "включи узбекский", "o'zbek tiliga o't"]
SWITCH_TO_RU_PHRASES = ["переключись на русский", "включи русский", "rus tiliga o't"]


def speak_response(text, tts_params):
    """Эта функция теперь является оберткой, которая правильно вызывает tts.speak"""
    if not text or not isinstance(text, str):
        return

    # Распаковываем параметры из tts_params
    model, speaker, _, sample_rate = tts_params  # lang больше не передаем напрямую в speak

    # --- ИСПРАВЛЕННЫЙ ВЫЗОВ ---
    # Передаем model и text, а speaker и sample_rate как именованные аргументы
    tts.speak(model=model, text=text, speaker=speaker, sample_rate=sample_rate)


async def run_in_thread(blocking_func, *args):
    loop = asyncio.get_event_loop()
    func = functools.partial(blocking_func, *args)
    return await loop.run_in_executor(None, func)


async def speak_response_async(text, tts_params):
    return await run_in_thread(speak_response, text, tts_params)


async def listen_for_wake_word_async():
    return await run_in_thread(wake_word_detector.listen_for_wake_word)


async def stt_listen_async(model):
    return await run_in_thread(stt.listen, model)


async def proactive_task(state, vision_task_queue, vision_result_queue):
    while True:
        await asyncio.sleep(PROACTIVE_INTERVAL_SECONDS)
        if state['in_conversation_mode']:
            continue

        print("\n[PROACTIVE_TASK] Запуск фоновой проверки...")
        vision_task_queue.put("analyze")
        try:
            detected_people = vision_result_queue.get_nowait()
            print("[PROACTIVE_TASK] Получен результат анализа зрения!")
            genders_in_car = {p.get('gender', 'Unknown') for p in detected_people}
            current_character = state['current_character']
            tts_params = state['tts_params']

            if 'Woman' in genders_in_car and current_character != 'lovelas':
                print("[ADAPT] Обнаружена девушка! -> Режим 'Ловелас'.")
                state['current_character'] = 'lovelas'
                state['listening_mode'] = 'CONSTANT'
                llm_handler.reload_chat_session(prompt.PROMPTS_BY_CHARACTER['lovelas'])
                await speak_response_async("Так-так... Кажется, обстановка накаляется. Включаю режим обаяния.",
                                           tts_params)

            elif 'Woman' not in genders_in_car and current_character == 'lovelas':
                print("[ADAPT] Девушек больше нет. -> Режим 'Дерзкий'.")
                state['current_character'] = 'derzkiy'
                state['listening_mode'] = 'WAKE_WORD'
                llm_handler.reload_chat_session(prompt.PROMPTS_BY_CHARACTER['derzkiy'])
                await speak_response_async("Ладно, шоу окончено. Снова в деле.", tts_params)

            if detected_people:
                unknown_person = next((p for p in detected_people if p['status'] == 'unknown'), None)
                if unknown_person and state['current_character'] == 'lovelas':
                    gender = "женщина" if unknown_person.get('gender') == 'Woman' else "мужчина"
                    internal_prompt = f"[ВНУТРЕННЕЕ СОБЫТИЕ: обнаружен НЕЗНАКОМЕЦ. ПОЛ: {gender}, ВОЗРАСТ: ~{unknown_person.get('age')}, ЭМОЦИЯ: {unknown_person.get('emotion')}]"
                    action = await llm_handler.get_mrx_action_async(internal_prompt)
                    await speak_response_async(action.get('response'), tts_params)
                    state['in_conversation_mode'] = True
        except queue.Empty:
            print("[PROACTIVE_TASK] Результат анализа зрения пока не готов.")
            pass


async def main():
    # --- ИНИЦИАЛИЗАЦИЯ СИСТЕМ ---
    print("Инициализация очередей и процесса для Vision...")
    vision_task_queue = mp.Queue()
    vision_result_queue = mp.Queue()

    vision_proc = mp.Process(target=vision_worker.vision_process_worker, args=(vision_task_queue, vision_result_queue))
    vision_proc.start()
    sfx_player.initialize_sfx()
    language_manager.init_language_system(llm_handler, prompt)
    wake_word_detector.initialize_detector()
    obd_manager.initialize()
    arduino_com.initialize()
    profile_manager.load_driver_profile('guest')

    state = {
        'current_character': 'derzkiy',
        'listening_mode': 'WAKE_WORD',
        'in_conversation_mode': False,
        'tts_params': language_manager.get_current_tts_params()
    }

    driver_name = profile_manager.get_current_driver_name()
    greeting = personality.get_dynamic_greeting(state['current_character'], driver_name)
    await speak_response_async(greeting, state['tts_params'])

    proactive_checker = asyncio.create_task(proactive_task(state, vision_task_queue, vision_result_queue))

    try:
        # --- ОСНОВНОЙ АСИНХРОННЫЙ ЦИКЛ ---
        while True:
            user_text = None
            vosk_model = language_manager.get_current_stt_model()

            if state['listening_mode'] == 'WAKE_WORD' and not state['in_conversation_mode']:
                print(f"\n[INFO] Режим '{state['current_character']}': Ожидание активации (Porcupine)...")
                await listen_for_wake_word_async()
                await speak_response_async("Слушаю", state['tts_params'])

            # --- АВТОМАТИЧЕСКАЯ ПАУЗА МУЗЫКИ ---
            media_player.pause_if_playing()

            # --- 1. РАСПОЗНАВАНИЕ РЕЧИ (STT) ---
            user_text = await stt_listen_async(vosk_model)

            if not user_text:
                media_player.resume_if_was_paused()
                continue

            if state['in_conversation_mode']:
                state['in_conversation_mode'] = False

            # --- ОБРАБОТКА КОМАНДЫ ВЫХОДА ---
            user_text_lower = user_text.lower()
            if any(fuzz.partial_ratio(user_text_lower, phrase) > EXIT_PHRASES_THRESHOLD for phrase in EXIT_PHRASES):
                await speak_response_async("Понял. Отключаюсь.", state['tts_params'])
                break

            # --- БЛОК ОБРАТНОЙ СВЯЗИ ---
            sfx_player.play_sfx('blip')
            await asyncio.sleep(0.3)

            filler_phrase = personality.get_filler_phrase(state['current_character'], user_text)

            filler_task = asyncio.create_task(speak_response_async(filler_phrase, state['tts_params']))

            async def get_brain_action():
                if network_manager.is_internet_available():
                    car_state = obd_manager.get_car_state()
                    context = f"[ДАННЫЕ АВТО: Обороты: {car_state.get('rpm', 'N/A')} RPM] [ЗАПРОС: {user_text}]"
                    return await llm_handler.get_mrx_action_async(context)
                else:
                    return offline_handler.recognize_command(user_text)

            brain_task = asyncio.create_task(get_brain_action())

            _, action = await asyncio.gather(filler_task, brain_task)

            if action is None:
                action = {'command': 'no_command',
                          'response': "Прости, я не понял тебя, а мой основной мозг сейчас не в сети."}

            # --- ОБРАБОТКА МУЗЫКАЛЬНЫХ И ДРУГИХ КОМАНД ---
            response_to_speak = action.get('response', 'Что-то пошло не так...')
            command = action.get('command', 'error')

            if command.startswith("music_play:"):
                search_query = command.split(":", 1)[1].strip()
                if search_query:
                    response_to_speak = await media_player.play_youtube_search(search_query)
                else:
                    response_to_speak = "Что именно ты хочешь включить?"
            elif command == "music_stop":
                response_to_speak = media_player.stop()

            print(f"[BRAIN] Команда: '{command}', Ответ для озвучки: '{response_to_speak}'")

            # --- 3. СИНТЕЗ И ВОСПРОИЗВЕДЕНИЕ ОСНОВНОГО ОТВЕТА (TTS) ---
            await speak_response_async(response_to_speak, state['tts_params'])

            # --- ВЫПОЛНЕНИЕ НЕ-МУЗЫКАЛЬНЫХ КОМАНД ---
            INTERNAL_COMMANDS = ['error', 'no_command', 'ask_clarification', 'set_character', 'set_voice',
                                 'listening_mode_set', 'vision_learn_person']
            is_internal = command in INTERNAL_COMMANDS or command.startswith(('memory', 'profile', 'contact', 'music_'))

            if not is_internal:
                arduino_com.send_command(command)

            if command == 'run_diagnostics':
                diagnostics_report = obd_manager.run_full_diagnostics()
                report_for_llm = f"[РЕЗУЛЬТАТЫ ДИАГНОСТИКИ: {diagnostics_report}]"
                final_action = await llm_handler.get_mrx_action_async(report_for_llm)
                await speak_response_async(final_action.get('response'), state['tts_params'])

            if command == 'ask_clarification':
                state['in_conversation_mode'] = True

            # --- АВТОМАТИЧЕСКОЕ ВОЗОБНОВЛЕНИЕ МУЗЫКИ ---
            if not command.startswith("music_"):
                media_player.resume_if_was_paused()

    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\nПрограмма завершается.")
    finally:
        print("Останавливаю фоновые задачи и процессы...")
        media_player.stop()  # <-- ОСТАНАВЛИВАЕМ МУЗЫКУ ПРИ ВЫХОДЕ
        proactive_checker.cancel()
        vision_task_queue.put("shutdown")
        vision_proc.join(timeout=5)
        if vision_proc.is_alive():
            vision_proc.terminate()
        arduino_com.close()
        print("MRX отключен.")


if __name__ == "__main__":
    mp.set_start_method('spawn', force=True)
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\nПрограмма была прервана пользователем.")