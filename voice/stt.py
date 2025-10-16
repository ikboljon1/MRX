# voice/stt.py (ФИНАЛЬНАЯ ВЕРСИЯ 3.0: Полностью оффлайн, правильный CHUNK_SIZE)
import torch
import sounddevice as sd
import vosk
import json
import numpy as np
import time
import os  # <-- Добавляем os для работы с путями

# --- НАСТРОЙКИ ---
SAMPLE_RATE = 16000
# _ИСПРАВЛЕНО_: Устанавливаем CHUNK_SIZE, который требует Silero VAD для 16000 Гц
CHUNK_SIZE = 512

# --- Умное определение пути к проекту ---
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- ЗАГРУЗКА VAD МОДЕЛИ (полностью оффлайн) ---
_vad_model, _utils = None, None
try:
    print("Загрузка модели Silero VAD из локального репозитория...")
    # _ИСПРАВЛЕНО_: Используем тот же оффлайн-подход, что и для TTS
    local_repo_path = os.path.join(_PROJECT_ROOT, 'snakers4_silero-vad_master')

    if not os.path.exists(local_repo_path):
        print(f"!!! ОШИБКА: Локальный репозиторий Silero VAD не найден по пути: {local_repo_path}")
        print("!!! Запустите программу один раз с доступом в интернет, чтобы он скачался.")
        # Первый раз оставляем возможность скачать
        torch.hub.set_dir('.')
        _vad_model, _utils = torch.hub.load(repo_or_dir='snakers4_silero-vad', model='silero_vad')
    else:
        _vad_model, _utils = torch.hub.load(repo_or_dir=local_repo_path,
                                            model='silero_vad',
                                            source='local')
    print("Модель Silero VAD успешно загружена.")
except Exception as e:
    print(f"КРИТИЧЕСКАЯ ОШИБКА при загрузке Silero VAD: {e}")

(get_speech_timestamps, _, _, VADIterator, _) = _utils


def listen(vosk_model_obj):
    if not vosk_model_obj or not _vad_model:
        print("ОШИБКА: Одна из моделей (Vosk или VAD) не загружена.")
        return ""

    recognizer = vosk.KaldiRecognizer(vosk_model_obj, SAMPLE_RATE)
    vad_iterator = VADIterator(_vad_model)

    print(f"\nСлушаю (Silero VAD + Vosk)... Говорите.")

    with sd.InputStream(samplerate=SAMPLE_RATE, blocksize=CHUNK_SIZE, device=None, dtype='float32',
                        channels=1) as stream:

        while True:  # Ждем начала речи
            audio_chunk, _ = stream.read(CHUNK_SIZE)
            audio_chunk_tensor = torch.from_numpy(audio_chunk.flatten())
            speech_dict = vad_iterator(audio_chunk_tensor, return_seconds=True)
            if speech_dict and 'start' in speech_dict:
                print("-> Речь обнаружена...")
                break

        start_time = time.perf_counter()

        first_chunk_int16 = (audio_chunk * 32768).astype(np.int16)
        recognizer.AcceptWaveform(first_chunk_int16.tobytes())

        while True:  # Слушаем до конца речи
            audio_chunk, _ = stream.read(CHUNK_SIZE)
            audio_chunk_int16 = (audio_chunk * 32768).astype(np.int16)
            recognizer.AcceptWaveform(audio_chunk_int16.tobytes())

            audio_chunk_tensor = torch.from_numpy(audio_chunk.flatten())
            speech_dict = vad_iterator(audio_chunk_tensor, return_seconds=True)
            if speech_dict and 'end' in speech_dict:
                print("-> Тишина, конец фразы.")
                vad_iterator.reset_states()
                break

    end_time = time.perf_counter()
    print(f"[PERF] Прослушивание и VAD заняли: {end_time - start_time:.4f} сек.")

    result_json = recognizer.FinalResult()
    result_dict = json.loads(result_json)
    text = result_dict.get('text', '')

    if text:
        print(f"Распознано (Vosk): '{text}'")
    else:
        print("Ничего не распознано.")

    return text