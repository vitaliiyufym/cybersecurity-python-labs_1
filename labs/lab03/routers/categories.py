"""Маршрути для категорій."""

from fastapi import APIRouter, Path, Response

from labs.lab03 import repository
from labs.lab03.routers.errors import RESPONSES_404, RESPONSES_409, call_repository
from labs.lab03.schemas import CategoryCreate, CategoryRead

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get(
    "",
    response_model=list[CategoryRead],
    summary="Список категорій",
)
def list_categories() -> list[dict]:
    """Повернути всі категорії за зростанням id."""
    return call_repository(repository.list_categories)


@router.post(
    "",
    response_model=CategoryRead,
    status_code=201,
    responses=RESPONSES_409,
    summary="Створити категорію",
)
def create_category(payload: CategoryCreate) -> dict:
    """Створити категорію; дублікат назви дає 409."""
    return call_repository(repository.create_category, payload.name)


@router.delete(
    "/{category_id}",
    status_code=204,
    responses={**RESPONSES_404, **RESPONSES_409},
    summary="Видалити порожню категорію",
)
def delete_category(
    category_id: int = Path(gt=0, description="Ідентифікатор категорії"),
) -> Response:
    """Видалити категорію без записів."""
    call_repository(repository.delete_category, category_id)
    return Response(status_code=204)
