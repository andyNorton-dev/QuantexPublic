from typing import Optional, Dict
from pydantic import BaseModel


class TaskModel(BaseModel):
    id: Optional[int] = None
    task_type: str
    difficulty: str
    main_text: str
    additional_text: str
    time: int
    progress: Optional[int] = None
    award: int
    access: int
    done: Optional[bool] = None
    valid: Optional[bool] = None
    url: Optional[str] = None
    type: Optional[str] = None

    class Config:
        from_attributes = True

class DailyModel(BaseModel):
    day: Optional[int] = None
    all_tasks: Optional[Dict[int, int]] = None

    class Config:
        from_attributes = True

class GameModel(BaseModel):
    game_name: str
    award: int
    points: Optional[int] = None

    class Config:
        from_attributes = True

