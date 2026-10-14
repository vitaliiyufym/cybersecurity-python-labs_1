"""Параметризовані SQL-запити до бази без залежності від FastAPI"""

import sqlite3
from contextlib import closing
from typing import Any

from labs.lab03.database import get_connection


class NotFoundError(Exception):
    """Запис або категорія не існує."""


class ConflictError(Exception):
    """Порушення унікальності або спроба видалити непорожню категорію."""


RECORD_SELECT = (
    "SELECT r.id, r.code, r.title, r.category_id, c.name AS category_name, "
    "r.value, r.status "
    "FROM records AS r JOIN categories AS c ON c.id = r.category_id"
)


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    """Перетворює рядок результату на словник."""
    return dict(row)


def _category_exists(connection: sqlite3.Connection, category_id: int) -> bool:
    """Перевіряє, що категорія існує."""
    row = connection.execute(
        "SELECT 1 FROM categories WHERE id = ?", (category_id,)
    ).fetchone()
    return row is not None


def _fetch_record(connection: sqlite3.Connection, record_id: int) -> dict[str, Any]:
    """Читає запис з назвою категорії або кинути NotFoundError."""
    row = connection.execute(RECORD_SELECT + " WHERE r.id = ?", (record_id,)).fetchone()
    if row is None:
        raise NotFoundError("Запис не знайдено")
    return _row_to_dict(row)


def _open() -> sqlite3.Connection:
    """Відкриває з'єднання з результатами у вигляді рядків-словників."""
    connection = get_connection()
    connection.row_factory = sqlite3.Row
    return connection


# категорії


def list_categories() -> list[dict[str, Any]]:
    """Повертає всі категорії за зростанням id."""
    with closing(_open()) as connection:
        rows = connection.execute(
            "SELECT id, name FROM categories ORDER BY id"
        ).fetchall()
    return [_row_to_dict(row) for row in rows]


def create_category(name: str) -> dict[str, Any]:
    """Створює категорію; дублікат назви дає ConflictError."""
    with closing(_open()) as connection:
        try:
            with connection:
                cursor = connection.execute(
                    "INSERT INTO categories (name) VALUES (?)", (name,)
                )
                category_id = cursor.lastrowid
        except sqlite3.IntegrityError as error:
            raise ConflictError("Категорія з такою назвою вже існує") from error
    return {"id": category_id, "name": name}


def delete_category(category_id: int) -> None:
    """Видаляє порожню категорію."""
    with closing(_open()) as connection:
        try:
            with connection:
                cursor = connection.execute(
                    "DELETE FROM categories WHERE id = ?", (category_id,)
                )
                deleted = cursor.rowcount
        except sqlite3.IntegrityError as error:
            raise ConflictError("Категорія містить записи") from error
    if deleted == 0:
        raise NotFoundError("Категорію не знайдено")


# записи


def create_record(data: dict[str, Any]) -> dict[str, Any]:
    """Створити один запис."""
    with closing(_open()) as connection:
        try:
            with connection:
                if not _category_exists(connection, data["category_id"]):
                    raise NotFoundError("Категорію не знайдено")
                cursor = connection.execute(
                    "INSERT INTO records (code, title, category_id, value, status) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (
                        data["code"],
                        data["title"],
                        data["category_id"],
                        data["value"],
                        data["status"],
                    ),
                )
                record_id = cursor.lastrowid
        except sqlite3.IntegrityError as error:
            raise ConflictError("Запис з таким code вже існує") from error
        return _fetch_record(connection, record_id)


def get_record(record_id: int) -> dict[str, Any]:
    """Отримати запис за id."""
    with closing(_open()) as connection:
        return _fetch_record(connection, record_id)


def list_records(
    category_id: int | None = None,
    status: str | None = None,
    min_value: float | None = None,
    q: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Список записів з фільтрами (AND), сортування за id, пагінація."""
    conditions: list[str] = []
    params: list[Any] = []
    if category_id is not None:
        conditions.append("r.category_id = ?")
        params.append(category_id)
    if status is not None:
        conditions.append("r.status = ?")
        params.append(status)
    if min_value is not None:
        conditions.append("r.value >= ?")
        params.append(min_value)
    if q is not None:
        conditions.append("instr(r.title, ?) > 0")
        params.append(q)

    sql = RECORD_SELECT
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY r.id ASC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with closing(_open()) as connection:
        rows = connection.execute(sql, params).fetchall()
    return [_row_to_dict(row) for row in rows]


def replace_record(record_id: int, data: dict[str, Any]) -> dict[str, Any]:
    """Повністю замінити змінювані поля запису; id не змінюється."""
    with closing(_open()) as connection:
        try:
            with connection:
                if not _category_exists(connection, data["category_id"]):
                    raise NotFoundError("Категорію не знайдено")
                cursor = connection.execute(
                    "UPDATE records SET code = ?, title = ?, category_id = ?, "
                    "value = ?, status = ? WHERE id = ?",
                    (
                        data["code"],
                        data["title"],
                        data["category_id"],
                        data["value"],
                        data["status"],
                        record_id,
                    ),
                )
                if cursor.rowcount == 0:
                    raise NotFoundError("Запис не знайдено")
        except sqlite3.IntegrityError as error:
            raise ConflictError("Запис з таким code вже існує") from error
        return _fetch_record(connection, record_id)


def delete_record(record_id: int) -> None:
    """Видалити запис."""
    with closing(_open()) as connection, connection:
        cursor = connection.execute("DELETE FROM records WHERE id = ?", (record_id,))
        deleted = cursor.rowcount
    if deleted == 0:
        raise NotFoundError("Запис не знайдено")


def create_records_bulk(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Атомарно додати пакет записів в одній транзакції."""
    with closing(_open()) as connection:
        try:
            with connection:
                new_ids: list[int] = []
                for item in items:
                    if not _category_exists(connection, item["category_id"]):
                        raise NotFoundError("Категорію не знайдено")
                    cursor = connection.execute(
                        "INSERT INTO records "
                        "(code, title, category_id, value, status) "
                        "VALUES (?, ?, ?, ?, ?)",
                        (
                            item["code"],
                            item["title"],
                            item["category_id"],
                            item["value"],
                            item["status"],
                        ),
                    )
                    new_ids.append(cursor.lastrowid)
        except sqlite3.IntegrityError as error:
            raise ConflictError("Дублікат code у пакеті або в базі") from error
        return [_fetch_record(connection, record_id) for record_id in new_ids]
