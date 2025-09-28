# services/weather.py
import requests

# --- ВАЖНО: Вставьте сюда ваш API ключ, который вы получили на сайте! ---
API_KEY = "618a4e3cf3cc1b1e73b0f8e03ca16a41"

BASE_URL = "http://api.openweathermap.org/data/2.5/weather"

# Словарь для перевода описания погоды с английского на русский
WEATHER_TRANSLATIONS = {
    'clear sky': 'ясно',
    'few clouds': 'малооблачно',
    'scattered clouds': 'облачно с прояснениями',
    'broken clouds': 'облачно',
    'overcast clouds': 'пасмурно',
    'shower rain': 'ливень',
    'rain': 'дождь',
    'light rain': 'небольшой дождь',
    'moderate rain': 'умеренный дождь',
    'thunderstorm': 'гроза',
    'snow': 'снег',
    'mist': 'туман',
    'smoke': 'дымка'
}


def get_weather(city_name):
    """
    Получает погоду для указанного города.
    Возвращает словарь с данными или None в случае ошибки.
    """
    # Формируем полный URL для запроса
    params = {
        'q': city_name,
        'appid': API_KEY,
        'units': 'metric',  # Получаем температуру в градусах Цельсия
        'lang': 'ru'  # Пытаемся получить описание на русском, но переведем сами для надежности
    }

    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()  # Проверяем, что запрос прошел успешно (код 200)

        data = response.json()

        # Извлекаем и форматируем только нужные нам данные
        description_en = data['weather'][0]['main'].lower()  # Берем основное описание
        if 'description' in data['weather'][0]:
            description_en = data['weather'][0]['description'].lower()

        weather_info = {
            'city': data['name'],
            'temperature': int(data['main']['temp']),
            'feels_like': int(data['main']['feels_like']),
            'description': WEATHER_TRANSLATIONS.get(description_en, description_en),  # Переводим
            'wind_speed': int(data['wind']['speed'])
        }
        print(f"Weather Service: Получены данные о погоде: {weather_info}")
        return weather_info

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"Weather Service ERROR: Город '{city_name}' не найден.")
        else:
            print(f"Weather Service ERROR: Ошибка HTTP {e.response.status_code}")
        return None
    except Exception as e:
        print(f"Weather Service ERROR: Произошла ошибка: {e}")
        return None


# --- Тест для запуска файла напрямую ---
if __name__ == '__main__':
    city = 'Джалал-Абад'
    weather = get_weather(city)
    if weather:
        print(f"\nПогода в городе {weather['city']}:")
        print(f"  Температура: {weather['temperature']}°C (ощущается как {weather['feels_like']}°C)")
        print(f"  Описание: {weather['description']}")
        print(f"  Скорость ветра: {weather['wind_speed']} м/с")