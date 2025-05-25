from enum import Enum
from pydantic import BaseModel
from typing import Optional

# Сначала создаем Pydantic модель для ответа
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
        from_attributes = True

class Academy(BaseModel):
    id: int
    type: str
    main_heading: str
    additional_heading: str
    avatar_url: str
    video_url: str
    rating: float
    level: str
    views: int
    time: int
    class Config:
        from_attributes = True

class AcademyFull(Academy):
    topic: str
    text: str

class AcademySortType(str, Enum):
    ARTICLE = "article"
    VIDEO = "video"

class AcademySort(BaseModel):
    type: Optional[AcademySortType] = None
    topic: Optional[str] = None

