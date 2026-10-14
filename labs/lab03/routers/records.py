"""Маршрути для записів."""

from typing import Annotated

from fastapi import APIRouter, Body, Path, Query, Response

from labs.lab03 import repository
from labs.lab03.config import VALUE_MAX, VALUE_MIN
from labs.lab03.routers.errors import RESPONSES_404, RESPONSES_409, call_repository
from labs.lab03.schemas import RecordCreate, RecordRead, RecordReplace, Status

router = APIRouter(prefix="/records", tags=["records"])

RecordId = Annotated[int, Path(gt=0, description="Ідентифікатор запису")]


@router.get(
    "",
    response_model=list[RecordRead],
    summary="Список записів із фільтрами",
)
def list_records(
    category_id: Annotated[
        int | None, Query(gt=0, description="Лише ця категорія")
    ] = None,
    status: Annotated[Status | None, Query(description="Лише цей статус")] = None,
    min_value: Annotated[
        float | None,
        Query(
            ge=VALUE_MIN,
            le=VALUE_MAX,
            allow_inf_nan=False,
            description="value >= min_value (відсотки)",
        ),
    ] = None,
    q: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=120,
            description="Буквальний підрядок у title (з урахуванням регістру)",
        ),
    ] = None,
    limit: Annotated[
        int, Query(ge=1, le=100, description="Макс. кількість записів")
    ] = 20,
    offset: Annotated[int, Query(ge=0, description="Скільки записів пропустити")] = 0,
) -> list[dict]:
    """Повернути записи, відфільтровані за AND, відсортовані за id."""
    return call_repository(
        repository.list_records,
        category_id=category_id,
        status=status,
        min_value=min_value,
        q=q,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/bulk",
    response_model=list[RecordRead],
    status_code=201,
    responses={**RESPONSES_404, **RESPONSES_409},
    summary="Пакетне створення записів",
)
def create_records_bulk(
    payload: Annotated[list[RecordCreate], Body(min_length=1, max_length=100)],
) -> list[dict]:
    """Атомарно створити від 1 до 100 записів: або всі, або жодного."""
    items = [item.model_dump() for item in payload]
    return call_repository(repository.create_records_bulk, items)


@router.post(
    "",
    response_model=RecordRead,
    status_code=201,
    responses={**RESPONSES_404, **RESPONSES_409},
    summary="Створити запис",
)
def create_record(payload: RecordCreate) -> dict:
    """Створити запис; id задає база."""
    return call_repository(repository.create_record, payload.model_dump())


@router.get(
    "/{record_id}",
    response_model=RecordRead,
    responses=RESPONSES_404,
    summary="Отримати запис",
)
def get_record(record_id: RecordId) -> dict:
    """Повернути один запис за id."""
    return call_repository(repository.get_record, record_id)


@router.put(
    "/{record_id}",
    response_model=RecordRead,
    responses={**RESPONSES_404, **RESPONSES_409},
    summary="Замінити запис",
)
def replace_record(record_id: RecordId, payload: RecordReplace) -> dict:
    """Повністю замінити змінювані поля запису."""
    return call_repository(repository.replace_record, record_id, payload.model_dump())


@router.delete(
    "/{record_id}",
    status_code=204,
    responses=RESPONSES_404,
    summary="Видалити запис",
)
def delete_record(record_id: RecordId) -> Response:
    """Видалити запис за id."""
    call_repository(repository.delete_record, record_id)
    return Response(status_code=204)
