import pygame
import os

_SFX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sfx')

# Словарь для хранения загруженных звуков
sounds = {}

def initialize_sfx():
    """Инициализирует микшер Pygame и предзагружает звуки."""
    try:
        pygame.mixer.init()
        print("[SFX] Звуковой движок инициализирован.")
        # Предзагружаем все звуки из папки sfx
        for f in os.listdir(_SFX_DIR):
            if f.endswith(('.wav', '.mp3')):
                sound_name = os.path.splitext(f)[0]
                sounds[sound_name] = pygame.mixer.Sound(os.path.join(_SFX_DIR, f))
        print(f"[SFX] Загружены звуки: {list(sounds.keys())}")
    except Exception as e:
        print(f"[SFX ERROR] Не удалось инициализировать Pygame Mixer: {e}")

def play_sfx(name, loop=False):
    """Воспроизводит звуковой эффект по имени."""
    if name in sounds:
        loops = -1 if loop else 0
        sounds[name].play(loops=loops)
    else:
        print(f"[SFX WARN] Звук '{name}' не найден.")

def stop_sfx(name):
    """Останавливает воспроизведение звукового эффекта."""
    if name in sounds:
        sounds[name].stop()