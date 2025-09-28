# hardware/music_player.py (Версия 2.0 с умным кэшем)

import os
import subprocess
import threading
import json
import random
from yt_dlp import YoutubeDL

# --- Настройки ---
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MUSIC_CACHE_DIR = os.path.join(_PROJECT_ROOT, 'music_cache')
os.makedirs(MUSIC_CACHE_DIR, exist_ok=True)
MAX_CACHE_PER_STATION = 10  # Сколько треков хранить для каждой станции

_player_process = None
_current_station = None
_playlist = []


# --- Основные функции плеера ---

def play_next_track():
    """Воспроизводит следующий трек из текущего плейлиста."""
    global _playlist
    if not _playlist:
        print("Music Player: Плейлист пуст, нечего играть.")
        # Можно попробовать пополнить кэш снова
        if _current_station:
            update_cache_for_station(_current_station)
        return

    track_path = random.choice(_playlist)
    _play_audio_file(track_path)


def _play_audio_file(filepath):
    """(Внутренняя) Воспроизводит аудиофайл."""
    global _player_process
    stop()
    if os.path.exists(filepath):
        print(f"Music Player: Воспроизведение файла {filepath}")
        _player_process = subprocess.Popen(['mpg123', '-q', filepath])
    else:
        print(f"Music Player ERROR: Файл не найден {filepath}")


def stop():
    """Останавливает воспроизведение музыки."""
    global _player_process, _current_station
    if _player_process:
        print("Music Player: Остановка воспроизведения.")
        _player_process.terminate()
        _player_process = None
    _current_station = None


def is_playing():
    """Проверяет, играет ли музыка."""
    return _player_process and _player_process.poll() is None


# --- Функции для работы с кэшем и YouTube ---

def preload_all_stations(stations):
    """ЗАПУСКАЕТСЯ ПРИ СТАРТЕ. Предзагружает треки для всех станций в фоне."""
    if not stations:
        return
    print("Music Player: Начало фоновой предзагрузки радиостанций...")
    for station_name, search_query in stations.items():
        thread = threading.Thread(target=update_cache_for_station, args=(search_query,))
        thread.start()


def play_station(search_query):
    """Начинает воспроизведение радиостанции."""
    global _current_station, _playlist
    _current_station = search_query

    station_dir = os.path.join(MUSIC_CACHE_DIR, search_query.replace(' ', '_'))
    if not os.path.exists(station_dir) or not os.listdir(station_dir):
        print(f"Music Player: Кэш для станции '{search_query}' пуст. Начинаю скачивание...")
        update_cache_for_station(search_query)  # Скачиваем первый раз
        # Нужно подождать, пока хотя бы один трек скачается
        # TODO: Реализовать более изящное ожидание
        time.sleep(10)

    _playlist = [os.path.join(station_dir, f) for f in os.listdir(station_dir)]
    play_next_track()

    # В фоне пополняем кэш
    threading.Thread(target=update_cache_for_station, args=(search_query,)).start()


def update_cache_for_station(search_query):
    """Скачивает треки для станции, если их меньше MAX_CACHE_PER_STATION."""
    station_dir = os.path.join(MUSIC_CACHE_DIR, search_query.replace(' ', '_'))
    os.makedirs(station_dir, exist_ok=True)

    current_tracks = os.listdir(station_dir)
    if len(current_tracks) >= MAX_CACHE_PER_STATION:
        print(f"Music Player: Кэш для '{search_query}' полон. Скачивание не требуется.")
        return

    print(f"Music Player: Обновление кэша для станции '{search_query}'...")
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}],
        'outtmpl': os.path.join(station_dir, '%(title)s.%(ext)s'),
        'playlistend': MAX_CACHE_PER_STATION,  # Скачиваем недостающие треки до лимита
        'ignoreerrors': True,
        'quiet': True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"ytsearch{MAX_CACHE_PER_STATION}:{search_query}"])
        print(f"Music Player: Кэш для '{search_query}' успешно обновлен.")
    except Exception as e:
        print(f"Music Player ERROR при обновлении кэша: {e}")