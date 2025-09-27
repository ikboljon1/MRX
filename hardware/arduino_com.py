# mrx_project/hardware/arduino_com.py

def send_command(command):
    """
    Это заглушка для отправки команд на Arduino.
    Вместо реальной отправки она просто печатает команду в консоль.
    """
    # Мы печатаем только те команды, которые предназначены для железа
    # (то есть, не no_command, ask_clarification, error и т.д.)
    hardware_commands = [
        'ac_', 'set_temp', 'window_', 'doors_', 'lights_', 'run_diagnostics'
    ]

    is_hardware_command = any(command.startswith(prefix) for prefix in hardware_commands)

    if is_hardware_command:
        print("\n" + "=" * 40)
        print(f"==> [КОМАНДА ОТПРАВЛЕНА НА ARDUINO]: {command}")
        print("=" * 40)