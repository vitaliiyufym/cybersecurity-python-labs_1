"""Pydantic-моделі запитів і відповідей варіант 11 відсотки 0-100"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from labs.lab03.config import VALUE_MAX, VALUE_MIN

Status = Literal["new", "in_progress", "done"]


class CategoryCreate(BaseModel):
    """Дані для створення категорії."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(min_length=2, max_length=40, description="Назва категорії")


class CategoryRead(CategoryCreate):
    """Категорія у відповіді API."""

    id: int


class RecordCreate(BaseModel):
    """Дані для створення запису (id задає база)"""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    code: str = Field(min_length=3, max_length=40, description="Унікальний код")
    title: str = Field(min_length=3, max_length=120, description="Назва вимірювання")
    category_id: int = Field(gt=0, description="Ідентифікатор категорії")
    value: float = Field(
        ge=VALUE_MIN,
        le=VALUE_MAX,
        allow_inf_nan=False,
        description="Завантаження каналу, відсотки (0-100)",
    )
    status: Status = Field(description="Стан перевірки вимірювання")


class RecordReplace(RecordCreate):
    """Повна заміна змінюваних полів запису"""


class RecordRead(RecordCreate):
    """Запис у відповіді API."""

    id: int
    category_name: str
