# mrx_project/hardware/arduino_com.py (ФИНАЛЬНАЯ РАБОЧАЯ ВЕРСИЯ)

import serial
import time

# --- НАСТРОЙКИ ---
# ВАЖНО! Убедитесь, что здесь указан правильный COM-порт вашей Arduino.
# Для Raspberry Pi это будет, например, '/dev/ttyACM0' или '/dev/ttyUSB0'
# Для вашего компьютера это, скорее всего, 'COM4'.
COM_PORT = 'COM5'
BAUDRATE = 9600

# Глобальная переменная для хранения подключения
arduino = None

def initialize():
    """
    Инициализирует реальное соединение с Arduino.
    Вызывается один раз при старте main.py.
    """
    global arduino
    try:
        arduino = serial.Serial(port=COM_PORT, baudrate=BAUDRATE, timeout=1)
        # Даем Arduino 2 секунды на перезагрузку после установки соединения
        time.sleep(2)
        print(f"Arduino Com: Успешно подключились к Arduino на порту {COM_PORT}")
        # Читаем приветственное сообщение от Arduino, чтобы очистить буфер
        initial_message = arduino.readline().decode('utf-8').strip()
        print(f"Arduino Com: Получено приветствие от Arduino: '{initial_message}'")
        return True
    except serial.SerialException as e:
        print(f"Arduino Com ERROR: Не удалось подключиться к порту {COM_PORT}.")
        print("Arduino Com WARN: Все команды к Arduino будут игнорироваться.")
        arduino = None
        return False

def send_command(command_str):
    """
    Отправляет реальную текстовую команду на Arduino через COM-порт.
    """
    if arduino and arduino.is_open:
        try:
            # Формируем команду: добавляем символ новой строки в конце и кодируем в байты
            full_command = (command_str + '\n').encode('utf-8')
            arduino.write(full_command)
            print(f"Arduino Com: Отправлена реальная команда -> {command_str}")
        except Exception as e:
            print(f"Arduino Com ERROR: Ошибка при отправке команды: {e}")
    else:
        # Это нужно, чтобы программа не падала, если Arduino не подключена
        print(f"Arduino Com WARN: Соединение не установлено. Команда '{command_str}' проигнорирована.")

def close():
    """Закрывает соединение с Arduino при завершении программы."""
    if arduino and arduino.is_open:
        arduino.close()
        print("Arduino Com: Соединение закрыто.")