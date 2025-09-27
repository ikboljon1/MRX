# voice/stt.py (Версия с таймаутом)

import vosk
import sounddevice as sd
import json
import queue

q = queue.Queue()


def callback(indata, frames, time, status):
    """Эта функция вызывается для каждого блока аудио с микрофона."""
    if status:
        print(status, flush=True)
    q.put(bytes(indata))


def listen(vosk_model_obj, listen_timeout=3.0):  # Добавляем таймаут прослушивания
    """
    Слушает микрофон в течение `listen_timeout` секунд.
    Если распознана полная фраза, возвращает ее.
    Если таймаут истек, обрабатывает то, что было сказано, и возвращает результат.
    """
    if vosk_model_obj is None:
        print("ОШИБКА: Vosk модель не загружена. Не могу слушать.")
        return ""

    recognizer = vosk.KaldiRecognizer(vosk_model_obj, 16000)
    print(f"\nСлушаю на языке {vosk_model_obj.lang_name}...")

    # Используем `with`, чтобы микрофон гарантированно выключился
    with sd.RawInputStream(samplerate=16000, blocksize=8000, device=None,
                           dtype='int16', channels=1, callback=callback):

        while True:
            try:
                # Пытаемся получить данные из очереди в течение listen_timeout секунд
                data = q.get(timeout=listen_timeout)

                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    text = result.get('text', '')
                    if text:
                        print(f"Распознано: '{text}'")
                        return text
            except queue.Empty:
                # Если за `listen_timeout` секунд ничего не пришло, значит, тишина.
                # Выходим из цикла и обрабатываем "остатки" речи.
                # print("Таймаут прослушивания...")
                break

    # Обрабатываем то, что могло быть сказано в самом конце
    final_result = json.loads(recognizer.FinalResult())
    text = final_result.get('text', '')
    if text:
        print(f"Распознано (частично): '{text}'")

    return text