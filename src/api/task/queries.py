from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import insert, select, exists, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only, aliased
from typing import List

from db.models import Task, TaskDone, TransactionPoints, User, UserVoucher, Voucher
from api.task.shemas import TaskModel
from api.voucher.queries import get_user_inviters

async def select_all_tasks(db: AsyncSession, user_id: int) -> List[TaskModel]:
    query = (
        select(
            Task,
            exists()
            .select_from(TaskDone)
            .where(
                (TaskDone.task_id == Task.id) & 
                (TaskDone.user_id == user_id)
            )
            .label('is_done')
        )
    )
    result = await db.execute(query)
    rows = result.all()
    tasks = []
    for task, is_done in rows:
        task_dict = {
            "id": task.id,
            "task_type": task.task_type,
            "difficulty": task.difficulty,
            "main_text": task.main_text,
            "additional_text": task.additional_text,
            "time": task.time,
            "progress": task.progress,
            "award": task.award,
            "access": task.access,
            "done": is_done
        }
        tasks.append(TaskModel(**task_dict))
    return tasks

async def create_task_done(db: AsyncSession, task_id: int, user_id: int) -> None:
    task_done = TaskDone(task_id=task_id, user_id=user_id)
    db.add(task_done)
    await db.commit()
    await db.refresh(task_done)


async def get_task(db: AsyncSession, task_id: int, user_id: int) -> TaskModel:
    query = select(Task).where(Task.id == task_id)
    result = await db.execute(query)
    task = result.scalar_one_or_none()
    if task is None:
        return None
    return task

async def update_user_points(db: AsyncSession, user_id: int, points: int) -> None:
    query = update(User).where(User.id == user_id).values(points=User.points + points)
    await db.execute(query)
    await db.commit()

async def create_multiple_tasks(db: AsyncSession) -> None:
    tasks = [
        TaskModel( task_type="регистрация", difficulty="легко", main_text="Task 1", additional_text="Additional 1", time=30, progress=0, award=10, access=1),
        TaskModel( task_type="контент", difficulty="средне", main_text="Task 2", additional_text="Additional 2", time=45, progress=0, award=20, access=1),
        TaskModel( task_type="действие", difficulty="сложно", main_text="Task 3", additional_text="Additional 3", time=60, progress=0, award=30, access=1),
        TaskModel( task_type="действие", difficulty="средне", main_text="Набрать 10 очков в змейке", additional_text="Набрать 10 очков в змейке", time=30, progress=0, award=10, access=1),
        TaskModel( task_type="действие", difficulty="средне", main_text="Набрать 10 очков в 3 в ряд", additional_text="Набрать 10 очков в 3 в ряд", time=30, progress=0, award=10, access=1),
    ]
    new_tasks = []
    for task in tasks:
        task_dict = task.dict()
        task_dict.pop('done', None)
        new_tasks.append(Task(**task_dict))
    
    db.add_all(new_tasks)
    await db.commit()
    for task in new_tasks:
        await db.refresh(task)

async def update_daily_day(db: AsyncSession, user: User, award: int) -> None:
    query = update(User).where(User.id == user.id).values(daily_day=user.daily_day + 1, points=user.points + award, daily_at=datetime.now())
    await db.execute(query)
    await db.commit()

async def add_in_transaction_points(db: AsyncSession, user_id: int, amount: int, action_type: str, action_name: str | None = None, points: int = 0) -> None:
    query = insert(TransactionPoints).values(user_id=user_id, amount=amount, action_type=action_type, action_name=action_name, points_balance=points+amount)
    await db.execute(query)
    await db.commit()

async def get_voucher_by_id(db: AsyncSession, voucher_id: int) -> Voucher:
    query = select(Voucher).where(Voucher.id == voucher_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def update_snake_game_points(db: AsyncSession, user_id: int, points: int) -> None:
    query = update(User).where(User.id == user_id).values(snake_game_points=points)
    await db.execute(query)
    await db.commit()

async def update_three_in_row_points(db: AsyncSession, user_id: int, points: int) -> None:
    query = update(User).where(User.id == user_id).values(three_in_row_points=points)
    await db.execute(query)
    await db.commit()

async def check_task_done(db: AsyncSession, task_id: int, user_id: int) -> bool:
    query = (
        select(exists().where(
            (TaskDone.task_id == task_id) & 
            (TaskDone.user_id == user_id)
        ))
    )
    result = await db.execute(query)
    return result.scalar_one()

async def select_all_user_voucher(db: AsyncSession, user_id: int):
    query = select(UserVoucher).where(UserVoucher.user_id == user_id)
    result = await db.execute(query)
    return result.scalars().all()

async def add_point_bonus_inviter(db: AsyncSession, user: User, amount: int) -> None:
    inviters = await get_user_inviters(db, user)
    bonus_perhaps = {
        1: 0.2,
        2: 0.15,
        3: 0.07,
        4: 0.05,
        5: 0.03
    }
    line = 0
    for inviter in inviters:
        if inviters[inviter.id]:
            line += 1
            bonus = amount * bonus_perhaps[line]
            query = update(User).where(User.id == inviter.id).values(points=User.points + bonus)
            await add_in_transaction_points(db, inviter.id, bonus, 'ref_bonus', 'ref_bonus', bonus)
            await db.execute(query)
            await db.commit()









