# mrx_project/services/system_monitor.py
import subprocess
import psutil

# Порог температуры в градусах Цельсия, при котором будет выдаваться предупреждение
HIGH_TEMPERATURE_THRESHOLD = 75.0


def get_cpu_temperature():
    """Возвращает температуру процессора Raspberry Pi."""
    try:
        # Выполняем команду vcgencmd, которая доступна в Raspberry Pi OS
        temp_str = subprocess.check_output(['vcgencmd', 'measure_temp']).decode('UTF-8')
        # Результат будет в формате "temp=45.5'C", извлекаем число
        return float(temp_str.split('=')[1].split("'")[0])
    except (FileNotFoundError, IndexError, ValueError):
        # Если команда не найдена или вывод некорректен
        return None


def get_ram_usage():
    """Возвращает процент использования оперативной памяти."""
    return psutil.virtual_memory().percent


def check_system_health():
    """
    Проверяет ключевые параметры системы и возвращает статус.
    """
    temp = get_cpu_temperature()
    ram = get_ram_usage()

    status = {'temperature': temp, 'ram_percent': ram, 'warnings': []}

    if temp and temp > HIGH_TEMPERATURE_THRESHOLD:
        warning_msg = f"Внимание, температура процессора достигла {temp}°C! Возможен перегрев."
        status['warnings'].append(warning_msg)
        print(f"[HEALTH_MONITOR] {warning_msg}")

    return status