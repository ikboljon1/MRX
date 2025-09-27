# arduino_tester.py
import serial
import time

# ВАЖНО! Укажите здесь ваш COM-порт, который вы видели в Arduino IDE.
# Скорее всего, это 'COM4'
COM_PORT = 'COM4'
BAUDRATE = 9600

try:
    # Устанавливаем соединение с Arduino
    arduino = serial.Serial(port=COM_PORT, baudrate=BAUDRATE, timeout=1)
    # Даем Arduino секунду на "пробуждение" после подключения
    time.sleep(2)
    print(f"Успешно подключились к Arduino на порту {COM_PORT}")

    # Бесконечный цикл для мигания
    while True:
        # Отправляем команду 'on'
        print("Отправляю команду: on")
        arduino.write(b'on\n') # b'' - означает байтовую строку, \n - символ новой строки
        time.sleep(1) # Ждем 1 секунду

        # Отправляем команду 'off'
        print("Отправляю команду: off")
        arduino.write(b'off\n')
        time.sleep(1) # Ждем 1 секунду

except serial.SerialException as e:
    print(f"ОШИБКА: Не удалось подключиться к порту {COM_PORT}.")
    print("Возможные причины:")
    print("1. Arduino не подключена или выбран неверный порт.")
    print("2. Монитор порта в Arduino IDE открыт (он блокирует порт). Закройте его!")
    print(f"Подробности: {e}")

except KeyboardInterrupt:
    print("\nПрограмма завершена пользователем.")
    if 'arduino' in locals() and arduino.is_open:
        arduino.close() # Закрываем порт при выходе