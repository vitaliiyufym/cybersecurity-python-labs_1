"""Перетворення помилок шару даних на HTTP-помилки."""

import logging
import sqlite3
from collections.abc import Callable
from typing import Any, TypeVar

from fastapi import HTTPException

from labs.lab03.repository import ConflictError, NotFoundError

logger = logging.getLogger(__name__)

T = TypeVar("T")

RESPONSES_404 = {404: {"description": "Не знайдено"}}
RESPONSES_409 = {409: {"description": "Конфлікт даних"}}


def call_repository(function: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """виконує функцію шару даних і перетворює помилки на HTTPException."""
    try:
        return function(*args, **kwargs)
    except NotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except sqlite3.Error as error:
        logger.exception("Помилка бази даних")
        raise HTTPException(
            status_code=500, detail="Внутрішня помилка сервера"
        ) from error
