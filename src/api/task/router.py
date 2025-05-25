from fastapi import APIRouter, Depends, status, Header
from typing import List, Optional
from api.auth.validation import get_current_active_auth_user
from db.engine import get_db
from db.models import User
from sqlalchemy.ext.asyncio import AsyncSession

from api.task.service import TaskService
from api.task.shemas import DailyModel, GameModel, TaskModel


router = APIRouter(
    prefix="/task",
    tags=["task"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[TaskModel])
async def get_tasks(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_auth_user)):
    task_service = TaskService(db)
    return await task_service.get_tasks(user)

@router.post("/complete/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def complete_task(
    task_id: int,
    tg_hash: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_auth_user)
):
    task_service = TaskService(db)
    return await task_service.complete_task(task_id, tg_hash, user)

@router.get("/daily", response_model=DailyModel)
async def get_daily(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_auth_user)):
    task_service = TaskService(db)
    return await task_service.get_daily(user)

@router.get("/daily/done", status_code=status.HTTP_204_NO_CONTENT)
async def done_daily(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_auth_user)):
    task_service = TaskService(db)
    return await task_service.check_daily_task(user)


@router.post("/game/done", status_code=status.HTTP_204_NO_CONTENT)
async def get_game(game: GameModel, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_auth_user)):
    task_service = TaskService(db)
    return await task_service.done_game(game, user)


@router.get("/validate")
async def validate_task(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_auth_user)):
    task_service = TaskService(db)
    return await task_service.validate_task(user)

