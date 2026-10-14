"""FastAPI-застосунок: облік завантаження каналів зв'язку варіант 11"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from labs.lab03.config import (
    DOMAIN_DESCRIPTION,
    DOMAIN_NAME,
    THRESHOLD,
    UNIT,
    VALUE_MAX,
    VALUE_MIN,
)
from labs.lab03.database import initialize_database
from labs.lab03.routers import categories, records
from shared import student

DESCRIPTION = (
    f"{DOMAIN_DESCRIPTION}\n\n"
    f"**Одиниця вимірювання:** {UNIT}. "
    f"**Діапазон value:** {VALUE_MIN:g}-{VALUE_MAX:g}. "
    f"**Поріг:** {THRESHOLD:g} (лише описовий, логіка на його основі "
    "не реалізується). Усі дані навчальні."
)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Під час запуску створити відсутні таблиці, не чіпаючи дані."""
    initialize_database()
    yield


app = FastAPI(
    title=DOMAIN_NAME,
    description=DESCRIPTION,
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(categories.router)
app.include_router(records.router)


@app.get("/ping", summary="Перевірка доступності API", tags=["service"])
def ping() -> dict[str, str]:
    """Повернути статус доступності."""
    return {"status": "ok"}


@app.get("/student", summary="Дані студента", tags=["service"])
def get_student() -> dict[str, str | int]:
    """Повернути ПІБ, групу та номер варіанта."""
    return {
        "student_name": student.STUDENT_NAME,
        "group_name": student.GROUP_NAME,
        "variant_number": student.VARIANT_NUMBER,
    }
