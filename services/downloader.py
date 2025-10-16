# services/downloader.py
import os
from yt_dlp import YoutubeDL

def download_tracks(track_urls, download_path, archive_file):
    """Скачивает список треков."""
    if not track_urls:
        return

    print(f"[DOWNLOADER] Начинаю загрузку {len(track_urls)} треков в '{os.path.basename(download_path)}'...")
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
        'ignoreerrors': True,
        'download_archive': archive_file,
        'quiet': True,
        'no_warnings': True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download(track_urls)
    print(f"[DOWNLOADER] Загрузка в '{os.path.basename(download_path)}' завершена.")