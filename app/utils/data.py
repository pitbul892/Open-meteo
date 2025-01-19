import json

from constants import DATA_FILE


def read_data() -> dict:
    """Читать файл."""
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        # Если файла нет, создаём пустую структуру
        return {"cities": {}}


def write_data(data: dict) -> None:
    """Записать в файл."""
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
