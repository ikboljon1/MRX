# mrx_project/voice/wake_word_detector.py
import json
import queue
import sounddevice as sd
import vosk

q = queue.Queue()


def callback(indata, frames, time, status):
    if status: print(status, flush=True)
    q.put(bytes(indata))


def listen_with_wake_word(vosk_model_obj, wake_words):
    """
    Умный детектор. Ждет активационное слово.
    - Если после него идет команда, возвращает команду.
    - Если после него тишина, возвращает сигнал, что слово услышано.
    """
    recognizer = vosk.KaldiRecognizer(vosk_model_obj, 16000)
    print("\n" + "=" * 20 + "\nMRX в режиме ожидания...")

    with sd.RawInputStream(samplerate=16000, blocksize=8000, device=None,
                           dtype='int16', channels=1, callback=callback):
        while True:
            data = q.get()
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get('text', '').lower()

                for word in wake_words:
                    if word in text:
                        # Слово найдено! "Вырезаем" все, что идет после него.
                        command_part = text.split(word, 1)[1].strip()

                        # Очищаем очередь на всякий случай
                        with q.mutex:
                            q.queue.clear()

                        if command_part:
                            # Сценарий "Лиза, [команда]"
                            print(f"АКТИВАЦИЯ И КОМАНДА: '{command_part}'")
                            return {'status': 'detected_and_command', 'command': command_part}
                        else:
                            # Сценарий "Лиза" и тишина
                            print("АКТИВАЦИЯ: Только слово.")
                            return {'status': 'detected_only', 'command': None}
            # Мы больше не используем PartialResult, так как полная фраза надежнее