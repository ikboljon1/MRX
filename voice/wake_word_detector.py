# mrx_project/voice/wake_word_detector.py
import json
import queue
import sounddevice as sd
import vosk
# Используем тот же механизм прослушивания, что и в stt.py

q = queue.Queue()


def callback(indata, frames, time, status):
    """Callback-функция для микрофона."""
    if status:
        print(status, flush=True)
    q.put(bytes(indata))


def listen_for_wake_word(vosk_model_obj, wake_words):
    """
    Бесконечно слушает микрофон в фоне, пока не услышит одно из активационных слов.
    Возвращает True, как только слово найдено.
    """
    recognizer = vosk.KaldiRecognizer(vosk_model_obj, 16000)
    print("\n" + "=" * 20)
    print(f"MRX в режиме ожидания. Скажите '{wake_words[0]}' для активации...")
    print("=" * 20)

    with sd.RawInputStream(samplerate=16000, blocksize=8000, device=None,
                           dtype='int16', channels=1, callback=callback):
        while True:
            try:
                # Получаем данные из очереди без таймаута, ждем вечно
                data = q.get()

                # Используем PartialResult, чтобы реагировать мгновенно
                if recognizer.AcceptWaveform(data):
                    pass
                else:
                    partial_result = json.loads(recognizer.PartialResult())
                    partial_text = partial_result.get('partial', '').lower()

                    # Проверяем, есть ли в распознаваемой речи наше слово
                    if any(word in partial_text for word in wake_words):
                        print(f"АКТИВАЦИЯ! Услышано слово '{partial_text}'")
                        # Очищаем очередь, чтобы старые данные не попали в распознавание команды
                        with q.mutex:
                            q.queue.clear()
                        return True  # Выходим из функции и возвращаем успех
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Ошибка в цикле ожидания активационного слова: {e}")
                return False