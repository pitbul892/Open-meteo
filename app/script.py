import uvicorn
from fastapi import FastAPI, HTTPException, Query
from schemas.city import CityBase, CityDB
from services.weather import (get_weather, update_weather_for_all_cities,
                              weather_in_time_today)
from utils.data import read_data, write_data

app = FastAPI()


@app.get('/current_weather')
async def get_current_weather(latitude: float, longitude: float):
    """
    Получить текущую погоду по координатам.
    """
    return await get_weather(
        name=None,
        latitude=latitude,
        longitude=longitude
    )


@app.on_event('startup')
async def startup():
    """Запуск обновления погоды."""
    await update_weather_for_all_cities()


@app.post('/add_city', response_model=CityDB)
async def add_city(city: CityBase):
    """
    Добавить новый город в остлеживаемые.
    """
    data = read_data()
    # Проверка на наличие в файле
    if city.name in data['cities']:
        raise HTTPException(status_code=400, detail='Этот город уже добавлен.')
    data['cities'][city.name] = {
        'coordinates': (city.latitude, city.longitude),
        'weather': {}
    }
    write_data(data)
    # Получить погоду
    weather = await get_weather(
        name=city.name, latitude=city.latitude, longitude=city.longitude)
    return CityDB(name=city.name,
                  latitude=city.latitude,
                  longitude=city.longitude,
                  weather=weather
                  )


@app.get('/cities')
async def get_cities():
    """
    Получить названия отслеживаемых городов.
    """
    data = read_data()
    return list(data['cities'].keys())


@app.get('/weather_at_time')
async def get_weather_at_time(
    city_name: str = Query(
        ..., description='Название города', example='Moscow'),
    time: str = Query(
        ..., description='Время в формате ЧЧ:ММ', example='15:00'),
    parameters: str = Query(
        ...,
        description=('Парметры через запятую, выберите из '
                     '(temperature, humidity, wind_speed, precipitation)'
                     ),
        example='temperature, humidity, wind_speed')
):
    """
    Возвращает погоду для города в указанное время на текущий день.
    """
    return await weather_in_time_today(city_name, time, parameters)

if __name__ == "__main__":
    uvicorn.run("script:app", host="127.0.0.1", port=8000, reload=True)
