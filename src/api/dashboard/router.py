from typing import List
from fastapi import APIRouter, Depends

from api.auth.validation import get_current_active_auth_user
from api.dashboard.service import DashboardService
from api.dashboard.shemas import DashboardModel, DashboardSortModel, HistoryModel, PointsModel, ReferralProfitModel, ToolsModel, TotalBalanceModel, TotalProfitModel
from sqlalchemy.ext.asyncio import AsyncSession
from db.engine import get_db
from db.models import User


router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
    responses={404: {"description": "Not found"}},
)


@router.get("/total_balance", response_model=List[TotalBalanceModel])
async def get_total_balance(
    sort: DashboardSortModel = Depends(), 
    db: AsyncSession = Depends(get_db), 
    user: User = Depends(get_current_active_auth_user)
    ):
    service = DashboardService(db)
    return await service.get_total_balance(user, sort)

@router.get("/total_points", response_model=List[PointsModel])
async def get_total_points(
    sort: DashboardSortModel = Depends(), 
    db: AsyncSession = Depends(get_db), 
    user: User = Depends(get_current_active_auth_user)
    ):
    service = DashboardService(db)
    return await service.rerutn_total_points(user, sort)

@router.get("/total_profit", response_model=List[TotalProfitModel])
async def get_total_profit(sort: DashboardSortModel = Depends(), db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_auth_user)):
    service = DashboardService(db)
    return await service.get_total_profit(user, sort)

@router.get("/referral_profit", response_model=List[ReferralProfitModel])
async def get_referral_profit(sort: DashboardSortModel = Depends(), db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_auth_user)):
    service = DashboardService(db)
    return await service.get_referral_profit(user, sort)

@router.get("/", response_model=DashboardModel)
async def get_dashboard(sort: DashboardSortModel = Depends(), db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_auth_user)):
    service = DashboardService(db)
    return await service.get_dashboard(user, sort)

@router.get("/history", response_model=List[HistoryModel])
async def get_history( db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_auth_user)):
    service = DashboardService(db)
    return await service.get_history_for_all_time(user)







