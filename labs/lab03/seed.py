"""заповнення бази з seed.json."""

import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

from labs.lab03.config import VALUE_MAX, VALUE_MIN
from labs.lab03.database import get_connection, initialize_database

SEED_PATH = Path(__file__).resolve().parent / "data" / "seed.json"
ALLOWED_STATUSES = {"new", "in_progress", "done"}
EXPECTED_CATEGORIES = 3
EXPECTED_RECORDS = 8


class SeedError(Exception):
    """Помилка початкових даних."""


def load_seed(path: Path = SEED_PATH) -> dict[str, Any]:
    """завантажує JSON з початковими даними."""
    try:
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)
    except OSError as error:
        raise SeedError(f"Не вдалося прочитати файл {path.name}.") from error
    except json.JSONDecodeError as error:
        raise SeedError(f"Некоректний JSON у файлі {path.name}.") from error
    if not isinstance(data, dict):
        raise SeedError("Корінь JSON має бути об'єктом.")
    return data


def validate_seed(data: dict[str, Any]) -> None:
    """Перевіряє структуру та значення початкових даних."""
    categories = data.get("categories")
    records = data.get("records")
    if not isinstance(categories, list) or not isinstance(records, list):
        raise SeedError("Потрібні масиви 'categories' і 'records'.")
    if len(categories) != EXPECTED_CATEGORIES:
        raise SeedError(f"Очікується {EXPECTED_CATEGORIES} категорії.")
    if len(records) != EXPECTED_RECORDS:
        raise SeedError(f"Очікується {EXPECTED_RECORDS} записів.")

    category_ids: set[int] = set()
    for category in categories:
        category_id = category.get("id")
        name = category.get("name")
        if not isinstance(category_id, int) or category_id <= 0:
            raise SeedError("id категорії має бути додатним цілим.")
        if not isinstance(name, str) or not 2 <= len(name.strip()) <= 40:
            raise SeedError("Назва категорії має містити 2-40 символів.")
        category_ids.add(category_id)

    for record in records:
        code = record.get("code")
        title = record.get("title")
        value = record.get("value")
        status = record.get("status")
        if not isinstance(code, str) or not 3 <= len(code.strip()) <= 40:
            raise SeedError("code має містити 3-40 символів.")
        if not isinstance(title, str) or not 3 <= len(title.strip()) <= 120:
            raise SeedError("title має містити 3-120 символів.")
        if record.get("category_id") not in category_ids:
            raise SeedError(f"Запис {code}: невідома категорія.")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise SeedError(f"Запис {code}: value має бути числом.")
        if not VALUE_MIN <= value <= VALUE_MAX:
            raise SeedError(f"Запис {code}: value поза діапазоном.")
        if status not in ALLOWED_STATUSES:
            raise SeedError(f"Запис {code}: недозволений статус.")


def database_is_empty(connection: sqlite3.Connection) -> bool:
    """Перевіряє, що в обох таблицях немає даних."""
    categories = connection.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
    records = connection.execute("SELECT COUNT(*) FROM records").fetchone()[0]
    return categories == 0 and records == 0


def run_seed() -> None:
    """Заповнює порожню базу категорії й записи в одній транзакції."""
    data = load_seed()
    validate_seed(data)
    initialize_database()

    with closing(get_connection()) as connection:
        if not database_is_empty(connection):
            print("База вже містить дані: заповнення пропущено, змін немає.")
            return
        with connection:
            connection.executemany(
                "INSERT INTO categories (id, name) VALUES (?, ?)",
                [(item["id"], item["name"]) for item in data["categories"]],
            )
            connection.executemany(
                "INSERT INTO records (code, title, category_id, value, status) "
                "VALUES (?, ?, ?, ?, ?)",
                [
                    (
                        item["code"],
                        item["title"],
                        item["category_id"],
                        item["value"],
                        item["status"],
                    )
                    for item in data["records"]
                ],
            )
    print(
        f"Додано {len(data['categories'])} категорії та {len(data['records'])} записів."
    )


def main() -> None:
    """Запускає заповнення з виведенням зрозумілих повідомлень."""
    try:
        run_seed()
    except SeedError as error:
        print(f"Помилка початкових даних: {error}")
    except sqlite3.Error as error:
        print(f"Помилка бази даних, зміни скасовано: {error}")


if __name__ == "__main__":
    main()
