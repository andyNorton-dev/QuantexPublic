from fastapi import HTTPException
from api.academy.queries import AcademyResponse, create_rating_academy, select_academy_by_id, select_academy_by_topic, select_academy_by_type, select_academy_by_type_and_topic, select_all_academy, select_all_topics, update_academy_rating, update_academy_view
from api.academy.shemas import Academy, AcademyFull, AcademySort
from sqlalchemy.ext.asyncio import AsyncSession
from api.academy.queries import create_multiple_academy, example_academies
from pydantic import BaseModel

from db.models import User

class AcademyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_academy(self, sort: AcademySort) -> list[AcademyResponse]:
        # await create_multiple_academy(self.db, example_academies)
        if sort.type and sort.topic:
            academies = await select_academy_by_type_and_topic(self.db, sort.type, sort.topic)
        elif sort.type:
            academies = await select_academy_by_type(self.db, sort.type)
        elif sort.topic:
            academies = await select_academy_by_topic(self.db, sort.topic)
        else:
            academies = await select_all_academy(self.db)
        
        # Преобразуем SQLAlchemy модели в Pydantic модели
        return academies
        
    async def get_academy_by_id(self, id: int) -> AcademyFull:
        academy = await select_academy_by_id(self.db, id)
        if academy:
            return academy
        else:
            raise HTTPException(status_code=404, detail="Материал не найден")
    
    async def view_academy(self, material_id: int) -> None:
        academy = await select_academy_by_id(self.db, material_id)
        if academy:
            await update_academy_view(self.db, material_id)
        else:
            raise HTTPException(status_code=404, detail="Материал не найден")

    async def rating_academy(self, material_id: int, rating: int, user: User) -> None:
        academy = await select_academy_by_id(self.db, material_id)
        if academy:
            await create_rating_academy(self.db, material_id, rating, user)
            await update_academy_rating(self.db, material_id)
        else:
            raise HTTPException(status_code=404, detail="Материал не найден")
        

    async def get_topics(self) -> list[str]:
        topics = await select_all_topics(self.db)
        return topics
