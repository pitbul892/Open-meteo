import asyncio
from datetime import datetime
from typing import Optional

import httpx
from constants import API_URL, WEATHER_PARAMETRS
from fastapi import HTTPException
from utils.data import read_data, write_data


async def get_weather(
        latitude: float, longitude: float, name: Optional[str] = None):
    """Получить погоду в текущее время."""
    # Формируем параметры запроса
    params = {
        'latitude': latitude,
        'longitude': longitude,
        'current': ['temperature_2m', 'surface_pressure', 'wind_speed_10m'],
        'forecast_days': 1
    }
    # Получаем ответ от API
    async with httpx.AsyncClient() as client:
        response = await client.get(API_URL, params=params)
        data = response.json()
    current_weather = {
        'temperature': data['current']['temperature_2m'],  # Температура
        'wind_speed': data['current']['wind_speed_10m'],  # Скорость ветра
        'pressure': data['current']['surface_pressure'],  # Давление
    }
    # Для реализации первого метода, не нужно записывать данные в файл
    if name is not None:
        data = read_data()
        if name in data['cities']:
            data['cities'][name]['weather'] = current_weather
            write_data(data)

    return current_weather


async def weather_in_time_today(city_name: str, time: str, parameters: str):
    """Возвращает погоду для города в указанное время на текущий день."""
    # Координаты из нашего файла
    city_coordinates = await get_coordinates_for_city(city_name)
    latitude, longitude = city_coordinates
    # Создаем список из запрошенных ингредиентов
    # только в случае если каждый из них у нас в списке на выбор
    try:
        param_list = [
            WEATHER_PARAMETRS[param]
            for param in parameters.split(', ')
        ]
    except KeyError as e:
        raise HTTPException(
            status_code=400, detail=f'Парметр не найден: {e.args[0]}'
        )

    # Формируем параметры запроса
    params = {
        'latitude': latitude,
        'longitude': longitude,
        'hourly': param_list,
        'timezone': 'auto'
    }

    #  Получаем данные погоды
    async with httpx.AsyncClient() as client:
        response = await client.get(API_URL, params=params)
        data = response.json()

    target_time = datetime.strptime(time, '%H:%M')
    target_minutes = target_time.hour * 60 + target_time.minute

    # Получаем данные по погоде на этот день
    hourly_data = data["hourly"]
    # Преобразуем данные по каждому параметру в соответствующие значения
    result = {}
    print(data)
    for param in params['hourly']:
        param_data = hourly_data.get(param)
        if param_data:
            # Находим ближайшее значение для каждого параметра
            closest_time_index = min(
                range(len(param_data)),
                key=lambda i: abs(i * 60 - target_minutes)
            )  # Используем индекс времени как i
            result[param] = param_data[closest_time_index]
    return result


# Координаты из нашего файла
async def get_coordinates_for_city(city_name: str) -> tuple:
    data = read_data()
    # Проверяем, есть ли город в данных
    city_info = data.get('cities', {}).get(city_name)
    if not city_info:
        raise HTTPException(status_code=404, detail='Город не добавлен.')
    return tuple(city_info["coordinates"])


async def update_weather_for_all_cities():
    # Переходим к асинхронному выполнению
    data = read_data()
    tasks = []
    for city_name, city_info in data["cities"].items():
        # Добавляем задачу в список для параллельного выполнения
        tasks.append(get_weather(
            city_info["coordinates"][0],
            city_info["coordinates"][1],
            name=city_name
        ))
    # Ожидаем завершения всех задач
    await asyncio.gather(*tasks)
    # Запускаем повторно через 15 минут
    asyncio.create_task(repeat_weather_update())  # Асинхронная задержка


async def repeat_weather_update():
    await asyncio.sleep(900)  # Ожидаем 15 минут
    await update_weather_for_all_cities()
