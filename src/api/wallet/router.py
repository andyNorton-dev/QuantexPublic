from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from sqlalchemy.ext.asyncio import AsyncSession

from db.engine import get_db
from db.models import User
from api.auth.validation import get_current_active_auth_user
from api.wallet.schemas import (
    CreateWithdrawalRequest, CryptoCurrency, ExchangeRate_and_Balance_In, ExchangeRateModel, InfoWalletModel, StakingBonusesModel, StakingModel, TransactionListItem, NetworkType, UserStakingModel
)
from api.wallet.service import WalletService

router = APIRouter(
    prefix="/wallet",
    tags=["wallet"],
    responses={404: {"description": "Not found"}},
)


@router.get('/adress/{network}', description="Cоздает и/или возвращает адрес для указанной сети")
async def get_adress(
    network: NetworkType, 
    db: AsyncSession = Depends(get_db), 
    user: User = Depends(get_current_active_auth_user)
):
    wallet_service = WalletService(db)
    return await wallet_service.get_adress(network, user)

# @router.post('/deposit', description="Депозит средств на адрес")
# async def deposit(
#     request: CreateDepositRequest = Query(...),
#     db: AsyncSession = Depends(get_db),
#     user: User = Depends(get_current_active_auth_user)
# ):
#     wallet_service = WalletService(db)
#     return await wallet_service.deposit(request, user)

@router.post('/withdrawal',status_code=status.HTTP_204_NO_CONTENT, description="Вывод средств с адреса")
async def withdrawal(
    request: CreateWithdrawalRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_auth_user)
):
    wallet_service = WalletService(db)
    return await wallet_service.withdrawal(request, user)

@router.get('/transactions_history', response_model=List[TransactionListItem], description="Список транзакций")
async def transactions_history(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_auth_user)
):
    wallet_service = WalletService(db)
    return await wallet_service.transactions_history(user)

@router.get('/exhange_rate_and_balance', response_model=ExchangeRateModel, description="Курс обмена и баланс в нужной валюте и сети")
async def exhange_rate(
    request: ExchangeRate_and_Balance_In = Query(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_auth_user)
):
    wallet_service = WalletService(db)
    return await wallet_service.exhange_rate(request, user)

@router.post('/exchange', description="обмена")
async def exchange_rate(
    request: ExchangeRate_and_Balance_In = Query(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_auth_user)
):
    wallet_service = WalletService(db)
    return await wallet_service.exchange(request, user)

@router.get('/staking', description="Все предложения по стейкингу", response_model=List[StakingModel])
async def staking(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_auth_user)
):
    wallet_service = WalletService(db)
    return await wallet_service.staking(user)


@router.post('/staking', description="Создание стейкинга", response_model=UserStakingModel)
async def create_staking(
    staking_id: int,
    amount: float,
    month: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_auth_user)
):
    wallet_service = WalletService(db)
    return await wallet_service.create_staking(staking_id, amount, month, user)

@router.get('/staking/bonuses', description="Информация о бонусах стейкинга", response_model=StakingBonusesModel)
async def get_staking_bonuses(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_auth_user)
):
    wallet_service = WalletService(db)
    return await wallet_service.get_staking_bonuses(user)


@router.get('/user_staking', description="Список стейкингов пользователя", response_model=List[UserStakingModel])
async def user_staking(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_auth_user)
):
    wallet_service = WalletService(db)
    return await wallet_service.user_staking(user)

@router.get('/info_wallet', description="Информация о кошельке", response_model=InfoWalletModel)
async def info_wallet(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_auth_user)
):
    wallet_service = WalletService(db)
    return await wallet_service.get_info_wallet(user)

@router.get('/exchange_rate_on_usdt', description="Курс обмена на USDT", response_model=ExchangeRateModel)
async def exchange_rate_on_usdt(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_auth_user)
):
    wallet_service = WalletService(db)
    return await wallet_service.get_exchange_rate_on_usdt(user)
