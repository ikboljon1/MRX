# voice/stt.py (Версия с VAD)
import webrtcvad
import collections
import queue
import sounddevice as sd
import vosk
import json

# --- НАСТРОЙКИ VAD ---
VAD_AGGRESSIVENESS = 2  # от 0 (наименее агрессивный) до 3 (наиболее агрессивный)
FRAME_DURATION_MS = 30  # Длительность одного аудио-фрейма (VAD работает с 10, 20 или 30 мс)
SAMPLE_RATE = 16000
CHUNK_SIZE = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)
SILENCE_DURATION_S = 1.5  # Сколько секунд тишины считать концом фразы
MAX_RECORD_S = 10.0  # Максимальная длительность записи, чтобы не слушать вечно

q = queue.Queue()


def callback(indata, frames, time, status):
    if status:
        print(status, flush=True)
    q.put(bytes(indata))


def listen(vosk_model_obj):
    """
    Слушает микрофон, используя VAD для определения конца фразы.
    Возвращает распознанный текст.
    """
    if vosk_model_obj is None:
        print("ОШИБКА: Vosk модель не загружена. Не могу слушать.")
        return ""

    vad = webrtcvad.Vad(VAD_AGGRESSIVENESS)
    recognizer = vosk.KaldiRecognizer(vosk_model_obj, SAMPLE_RATE)

    padding_duration_ms = int(SILENCE_DURATION_S * 1000)
    ring_buffer_size = padding_duration_ms // FRAME_DURATION_MS
    ring_buffer = collections.deque(maxlen=ring_buffer_size)

    triggered = False
    voiced_frames = []

    print(f"\nСлушаю на языке {vosk_model_obj.lang_name} (режим VAD)... Говорите.")

    with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=CHUNK_SIZE, device=None,
                           dtype='int16', channels=1, callback=callback):

        num_silence_frames = 0
        max_frames = int(MAX_RECORD_S * SAMPLE_RATE / CHUNK_SIZE)

        for _ in range(max_frames):
            frame = q.get()
            is_speech = vad.is_speech(frame, SAMPLE_RATE)

            if not triggered:
                ring_buffer.append((frame, is_speech))
                if any(f[1] for f in ring_buffer):
                    triggered = True
                    print("-> Обнаружена речь, начинаю запись...")
                    for f, s in ring_buffer:
                        if s:
                            voiced_frames.append(f)
                    ring_buffer.clear()
            else:
                voiced_frames.append(frame)
                if not is_speech:
                    num_silence_frames += 1
                    if num_silence_frames * FRAME_DURATION_MS / 1000 > SILENCE_DURATION_S:
                        print("-> Обнаружена тишина, конец фразы.")
                        break
                else:
                    num_silence_frames = 0

    print("Обработка записанного фрагмента...")
    full_audio = b''.join(voiced_frames)
    recognizer.AcceptWaveform(full_audio)
    result = json.loads(recognizer.FinalResult())
    text = result.get('text', '')

    if text:
        print(f"Распознано (VAD): '{text}'")
    else:
        print("Ничего не распознано.")

    return text