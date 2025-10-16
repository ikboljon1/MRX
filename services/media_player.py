# services/media_player.py
import os
import asyncio
import subprocess
import signal
from yt_dlp import YoutubeDL

# --- НАСТРОЙКИ ---
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MUSIC_CACHE_DIR = os.path.join(_PROJECT_ROOT, 'music_cache', 'youtube_search')
os.makedirs(MUSIC_CACHE_DIR, exist_ok=True)

# --- ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ДЛЯ УПРАВЛЕНИЯ ПЛЕЕРОМ ---
player_process = None
was_paused_by_assistant = False

# --- ОСНОВНЫЕ ФУНКЦИИ УПРАВЛЕНИЯ ---

def is_playing():
    """Проверяет, жив ли процесс плеера и не на паузе ли он."""
    # player.poll() is None означает, что процесс еще не завершился.
    return player_process and player_process.poll() is None

def pause_if_playing():
    """Ставит музыку на паузу, если она играет. Используется ассистентом."""
    global was_paused_by_assistant
    if is_playing() and not was_paused_by_assistant:
        try:
            print("[MEDIA] Ассистент ставит музыку на паузу...")
            os.kill(player_process.pid, signal.SIGSTOP)
            was_paused_by_assistant = True
        except ProcessLookupError:
            # Процесс мог завершиться прямо перед вызовом
            pass

def resume_if_was_paused():
    """Возобновляет музыку, если она была поставлена на паузу ассистентом."""
    global was_paused_by_assistant
    if was_paused_by_assistant and is_playing():
        try:
            print("[MEDIA] Ассистент возобновляет музыку...")
            os.kill(player_process.pid, signal.SIGCONT)
            was_paused_by_assistant = False
        except ProcessLookupError:
            pass

def stop():
    """Полностью останавливает воспроизведение."""
    global player_process, was_paused_by_assistant
    if is_playing():
        print("[MEDIA] Музыка полностью остановлена.")
        # terminate() - более мягкий способ, чем kill()
        player_process.terminate()
        player_process = None
    was_paused_by_assistant = False
    return "Музыка остановлена."


async def play_youtube_search(query: str):
    """
    Ищет видео на YouTube, скачивает его и воспроизводит с помощью ffplay.
    """
    global player_process
    print(f"[MEDIA] Поиск на YouTube: '{query}'")

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(MUSIC_CACHE_DIR, '%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'default_search': 'ytsearch1',
    }

    loop = asyncio.get_event_loop()
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(
                None, lambda: ydl.extract_info(query, download=True)['entries'][0]
            )
            filename = ydl.prepare_filename(info)
            title = info.get('title', 'Неизвестный трек')

            print(f"[MEDIA] Файл готов к воспроизведению: {filename}")

            stop()  # Останавливаем предыдущий трек, если он был

            # Запускаем ffplay в фоновом режиме
            # -nodisp: не показывать окно с видео/визуализацией
            # -autoexit: закрыться после окончания трека
            # -loglevel quiet: не выводить лишнюю информацию
            player_process = subprocess.Popen(
                ['ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet', filename],
                # Перенаправляем вывод, чтобы не засорять консоль
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            return f"Включаю {title}"

    except Exception as e:
        print(f"[MEDIA ERROR] Ошибка при поиске/скачивании/воспроизведении: {e}")
        return "Прости, не смог найти или скачать этот трек."