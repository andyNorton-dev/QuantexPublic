from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, insert, select, update
from api.academy.shemas import AcademyFull, AcademySortType
from db.models import Academy, RatingAcademy, User
from pydantic import BaseModel
from typing import List, Optional, Dict


async def select_academy_by_type_and_topic(db: AsyncSession, type: str, topic: str) -> List[Academy]:
    query = select(Academy).where(Academy.type == type, Academy.topic == topic)
    result = await db.execute(query)
    return result.scalars().all()

async def select_academy_by_type(db: AsyncSession, type: str) -> List[Academy]:
    query = select(Academy).where(Academy.type == type)
    result = await db.execute(query)
    return result.scalars().all()

async def select_academy_by_topic(db: AsyncSession, topic: str) -> List[Academy]:
    query = select(Academy).where(Academy.topic == topic)
    result = await db.execute(query)
    return result.scalars().all()

async def select_all_academy(db: AsyncSession) -> List[Academy]:
    query = select(Academy)
    result = await db.execute(query)
    return result.scalars().all()

async def select_academy_by_id(db: AsyncSession, id: int) -> AcademyFull:
    query = select(Academy).where(Academy.id == id)
    result = await db.execute(query)
    academy = result.scalar_one_or_none()
    return academy

async def update_academy_view(db: AsyncSession, material_id: int) -> None:
    query = update(Academy).where(Academy.id == material_id).values(views=Academy.views + 1)
    await db.execute(query)
    await db.commit()

async def create_rating_academy(db: AsyncSession, material_id: int, rating: int, user: User) -> None:
    query = insert(RatingAcademy).values(academy_id=material_id, rating=rating, user_id=user.id)
    await db.execute(query)
    await db.commit()

async def update_academy_rating(db: AsyncSession, material_id: int) -> None:
    query = select(func.avg(RatingAcademy.rating)).where(RatingAcademy.academy_id == material_id)
    result = await db.execute(query)
    average_rating = result.scalar()
    
    update_query = update(Academy).where(Academy.id == material_id).values(rating=average_rating)
    await db.execute(update_query)
    await db.commit()

async def select_all_topics(db: AsyncSession) -> List[str]:
    query = select(Academy.topic).distinct()
    result = await db.execute(query)
    return result.scalars().all()

# Сначала создадим Pydantic модель для ответа
class AcademyResponse(BaseModel):
    id: Optional[int] = None
    type: str
    topic: str
    main_heading: str
    additional_heading: str
    avatar_url: str
    video_url: Optional[str] = None
    text: str
    rating: float
    level: str
    views: int
    time: int

    class Config:
        from_attributes = True  # Позволяет конвертировать из SQLAlchemy модели

async def create_multiple_academy(db: AsyncSession, academies: List[Dict]) -> None:
    new_academies = []
    for academy_data in academies:
        # Создаем объект SQLAlchemy модели Academy, а не Pydantic модели
        new_academy = Academy(
            type=academy_data['type'],
            topic=academy_data['topic'],
            main_heading=academy_data['main_heading'],
            additional_heading=academy_data['additional_heading'],
            avatar_url=academy_data['avatar_url'],
            video_url=academy_data['video_url'],
            text=academy_data['text'],
            rating=academy_data['rating'],
            level=academy_data['level'],
            views=academy_data['views'],
            time=academy_data['time']
        )
        new_academies.append(new_academy)
    
    db.add_all(new_academies)
    await db.commit()
    for academy in new_academies:
        await db.refresh(academy)

# Пример использования функции create_multiple_academy
# Пример данных для создания нескольких академий
example_academies = [
    {
        "type": "article",
        "topic": "Python",
        "main_heading": "Изучение Python",
        "additional_heading": "Основы Python",
        "avatar_url": "http://example.com/python.png",
        "video_url": "http://example.com/python_video.mp4",
        "text": "Полный курс по Python",
        "rating": 4.5,
        "level": "Начальный",
        "views": 100,
        "time": 120
    },
    {
        "type": "video",
        "topic": "Дизайн",
        "main_heading": "Основы графического дизайна",
        "additional_heading": "Работа с Photoshop",
        "avatar_url": "http://example.com/design.png",
        "video_url": "http://example.com/design_video.mp4",
        "text": "Курс по графическому дизайну",
        "rating": 4.7,
        "level": "Средний",
        "views": 150,
        "time": 90
    }
]



