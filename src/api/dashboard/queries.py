from typing import List
from sqlalchemy import select, desc, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import TransactionPoints, User, Transaction
from api.dashboard.shemas import PointsModel, TotalBalanceModel, SortOptions
from datetime import datetime, timedelta
from api.core.config import settings


async def select_total_balance(db: AsyncSession, user: User, hours: SortOptions) -> List[TotalBalanceModel]:
    if hours == SortOptions.all_time:
        query = select(Transaction).where(
            Transaction.user_id == user.id,
            or_(
                and_(Transaction.action_type == 'deposit', Transaction.currency == 'USDT'),
                and_(Transaction.action_type == 'exchange', Transaction.currency == 'USDT'),
                and_(Transaction.action_type == 'buy_voucher', Transaction.currency == 'USDT'),
                and_(Transaction.action_type == 'create_staking', Transaction.currency == 'USDT'),
                and_(Transaction.action_type == 'ref_bonus', Transaction.currency == 'USDT'),
                and_(Transaction.action_type == 'withdrawal', Transaction.currency == 'USDT')
            )
        ).order_by(Transaction.created_at)
    else:
        time_threshold = datetime.utcnow() - timedelta(hours=int(hours.value))
        query = select(Transaction).where(
            Transaction.user_id == user.id,
            Transaction.created_at >= time_threshold,
            or_(
                and_(Transaction.action_type == 'deposit', Transaction.currency == 'USDT'),
                and_(Transaction.action_type == 'exchange', Transaction.currency == 'USDT'),
                and_(Transaction.action_type == 'buy_voucher', Transaction.currency == 'USDT'),
                and_(Transaction.action_type == 'create_staking', Transaction.currency == 'USDT'),
                and_(Transaction.action_type == 'ref_bonus', Transaction.currency == 'USDT'),
                and_(Transaction.action_type == 'withdrawal', Transaction.currency == 'USDT')
            )
        ).order_by(Transaction.created_at)
    
    result = await db.execute(query)
    transactions = result.scalars().all()
    
    # Преобразуем Transaction в TotalBalanceModel
    balance_models = []
    for tx in transactions:
        balance_models.append(TotalBalanceModel(
            balance=tx.amount,
            date=tx.created_at,
            percent_change=0  # Начальное значение, будет обновлено в service
        ))
    
    return balance_models


async def select_referral_bonus(db: AsyncSession, user: User) -> List[TotalBalanceModel]:
    query = select(Transaction).where(
        Transaction.user_id == user.id,
        Transaction.action_type == 'ref_bonus'
    ).order_by(Transaction.created_at)

    result = await db.execute(query)
    transactions = result.scalars().all()
    balance_models = []
    for tx in transactions:
        balance_models.append(TotalBalanceModel(
            balance=tx.amount,
            date=tx.created_at,
            percent_change=0  # Начальное значение, будет обновлено в service
        ))

    return balance_models

async def select_list_transactions(db: AsyncSession, user: User, hours = SortOptions.all_time) -> List[Transaction]:
    if hours == SortOptions.all_time:
        query = select(Transaction).where(
            Transaction.user_id == user.id
        ).order_by(desc(Transaction.created_at))
    else:
        time_threshold = datetime.utcnow() - timedelta(hours=int(hours.value))
        query = select(Transaction).where(
            Transaction.user_id == user.id,
            Transaction.created_at >= time_threshold
        ).order_by(desc(Transaction.created_at))

    result = await db.execute(query)
    transactions = result.scalars().all()

    return transactions

async def select_total_points(db: AsyncSession, user: User, hours: SortOptions) -> List[PointsModel]:
    if hours == SortOptions.all_time:
        query = select(TransactionPoints).where(
            TransactionPoints.user_id == user.id
        ).order_by(TransactionPoints.date)
    else:
        time_threshold = datetime.utcnow() - timedelta(hours=int(hours.value))
        query = select(TransactionPoints).where(
            TransactionPoints.user_id == user.id,
            TransactionPoints.date >= time_threshold
        ).order_by(TransactionPoints.date)

    result = await db.execute(query)
    transactions = result.scalars().all()

    return transactions

async def select_win_games(db: AsyncSession, user: User) -> int:
    query = select(func.count()).select_from(TransactionPoints).where(
        TransactionPoints.user_id == user.id,
        TransactionPoints.action_type == settings.task_type.Game
    )

    result = await db.execute(query)
    count = result.scalar()
    
    return count or 0
