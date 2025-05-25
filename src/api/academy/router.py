from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.academy.queries import AcademyResponse
from api.academy.service import AcademyService
from api.auth.validation import get_current_active_auth_user
from db.engine import get_db
from api.academy.shemas import Academy, AcademyFull, AcademySort
from db.models import User


router = APIRouter(
    prefix="/academy",
    tags=["academy"],
    responses={404: {"description": "Материал не найден"}},
)


@router.get("/", response_model=List[AcademyResponse], description="Выводит все курсы")
async def get_academy(
    sort: AcademySort = Query(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_auth_user)
):
    academy_service = AcademyService(db)
    return await academy_service.get_academy(sort)

@router.get("/{id}", response_model=AcademyFull, description="Выводит курс по id")
async def get_academy_by_id(
    id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_auth_user)
):
    academy_service = AcademyService(db)
    return await academy_service.get_academy_by_id(id)

@router.post("/view/{material_id}", status_code=status.HTTP_204_NO_CONTENT, description="Добавляет просмотр курсу")
async def view_academy(
    material_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_auth_user)
):
    academy_service = AcademyService(db)
    return await academy_service.view_academy(material_id)

@router.post("/rating/{material_id}", status_code=status.HTTP_204_NO_CONTENT, description="Оценивает курс")
async def rating_academy(
    material_id: int,
    rating: float = Query(..., ge=0, le=5),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_auth_user)
):
    academy_service = AcademyService(db)
    return await academy_service.rating_academy(material_id, rating, user)

@router.get('/topics/', response_model=List[str], description="Выводит все темы")
async def get_topics(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_auth_user)
):
    academy_service = AcademyService(db)
    return await academy_service.get_topics()

