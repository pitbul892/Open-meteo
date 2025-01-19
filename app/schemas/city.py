from typing import Optional

from constants import MAX_LENGTH_NAME
from pydantic import BaseModel, Field
from pydantic.fields import Required


class CityBase(BaseModel):
    """Схема для запроса."""

    name: str = Field(
        Required, unique=True, min_length=1, max_length=MAX_LENGTH_NAME)
    latitude: float = Field(Required)
    longitude: float = Field(Required)


class CityDB(CityBase):
    """Схема для ответа."""

    weather: Optional[dict]
