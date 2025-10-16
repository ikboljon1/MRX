# mrx_project/services/network_manager.py
import subprocess
import socket
import time


def is_internet_available():
    """
    Проверяет наличие интернет-соединения, пытаясь подключиться к DNS Google.
    Надежный и быстрый способ.
    """
    try:
        # Пытаемся создать сокет-соединение с сервером Google на порту 80
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        print("[Network] Интернет-соединение доступно.")
        return True
    except OSError:
        pass
    print("[Network] ВНИМАНИЕ: Интернет-соединение отсутствует.")
    return False


def scan_wifi():
    """
    Сканирует доступные Wi-Fi сети с помощью nmcli.
    Возвращает список имен сетей (SSID).
    """
    print("[Network] Сканирование Wi-Fi сетей...")
    try:
        # Запускаем nmcli для сканирования и получения списка сетей
        # --terse для компактного вывода, --fields SSID для нужных полей
        # dev wifi rescan заставляет его обновить список
        subprocess.run(['nmcli', 'dev', 'wifi', 'rescan'], check=True, capture_output=True)
        time.sleep(3)  # Даем время на завершение сканирования

        result = subprocess.run(
            ['nmcli', '--terse', '--fields', 'SSID', 'dev', 'wifi', 'list'],
            check=True, capture_output=True, text=True
        )

        # Разбираем вывод. nmcli выдает список SSID, каждый на новой строке.
        # Убираем пустые строки, если они есть.
        ssids = [line.strip() for line in result.stdout.split('\n') if line.strip()]

        # Убираем дубликаты, сохраняя порядок
        unique_ssids = list(dict.fromkeys(ssids))

        print(f"[Network] Найдены сети: {unique_ssids}")
        return unique_ssids

    except subprocess.CalledProcessError as e:
        print(f"[Network ERROR] Ошибка при сканировании Wi-Fi: {e.stderr}")
        return []
    except FileNotFoundError:
        print("[Network ERROR] Утилита 'nmcli' не найдена. Убедитесь, что NetworkManager установлен.")
        return []


def connect_wifi(ssid, password=None):
    """
    Подключается к указанной Wi-Fi сети.
    Возвращает True в случае успеха, False в случае неудачи.
    """
    print(f"[Network] Попытка подключения к Wi-Fi сети: {ssid}")
    command = ['nmcli', 'dev', 'wifi', 'connect', ssid]
    if password:
        command.extend(['password', password])

    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        if "successfully activated" in result.stdout:
            print(f"[Network] Успешно подключено к сети {ssid}.")
            return True
        else:
            # На случай, если команда выполнилась, но подключения не произошло
            print(f"[Network WARN] Команда выполнена, но статус подключения неясен: {result.stdout}")
            # Дополнительно проверим наличие интернета через несколько секунд
            time.sleep(5)
            return is_internet_available()

    except subprocess.CalledProcessError as e:
        error_output = e.stderr.lower()
        print(f"[Network ERROR] Не удалось подключиться к {ssid}: {error_output}")
        # Возвращаем конкретную причину, если это неверный пароль
        if "secrets were required, but not provided" in error_output:
            return "password_required"
        if "invalid password" in error_output or "802.1x supplicant failed" in error_output:
            return "wrong_password"
        return False


# Функции для Bluetooth (можно расширить в будущем)
def scan_bluetooth():
    """Сканирует Bluetooth устройства (упрощенная версия)."""
    print("[Network] Сканирование Bluetooth... (функция не реализована полностью)")
    # Реализация потребует парсинга вывода 'bluetoothctl scan on'
    return ["Функция сканирования Bluetooth в разработке"]