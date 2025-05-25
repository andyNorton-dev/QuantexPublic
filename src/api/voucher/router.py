from typing import List
from fastapi import APIRouter
from fastapi import Depends
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from db.engine import get_db
from api.auth.validation import get_current_active_auth_user
from db.models import Market, User, UserVoucher, Voucher
from api.voucher.shemas import UserVoucherSchema, VoucherOut, Voucher
from api.voucher.service import VoucherService


router = APIRouter(
    prefix="/voucher",
    tags=["voucher"],
    responses={404: {"description": "Материал не найден"}},
)


@router.get("/", response_model=VoucherOut)
async def get_vouchers(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_auth_user)
):
    voucher_service = VoucherService(db)
    return await voucher_service.get_vouchers(user)

@router.post("/buy/{voucher_id}", status_code=status.HTTP_204_NO_CONTENT)
async def buy_voucher(
    voucher_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_auth_user)
):
    voucher_service = VoucherService(db)
    await voucher_service.buy_voucher(voucher_id, user)

@router.get('/marketplace', response_model=List[Voucher])
async def get_marketplace(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_auth_user)
):
    voucher_service = VoucherService(db)
    return await voucher_service.get_marketplace(user)

@router.post('/marketplace/sell/{voucher_id}', status_code= status.HTTP_204_NO_CONTENT)
async def sell_voucher(
    voucher_id: int,
    cost: float,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_auth_user)
):
    voucher_service = VoucherService(db)
    await voucher_service.sell_voucher(voucher_id, user, cost)

@router.get('/marketplace/buy/{voucher_id}', status_code=status.HTTP_204_NO_CONTENT)
async def buy_voucher_from_marketplace(
    voucher_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_auth_user)
):
    voucher_service = VoucherService(db)
    await voucher_service.buy_voucher_from_marketplace(voucher_id, user)

@router.get('/marketplace/cancel/{voucher_id}', status_code=status.HTTP_204_NO_CONTENT)
async def cancel_marketplace(
    voucher_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_auth_user)
):
    voucher_service = VoucherService(db)
    await voucher_service.cancel_marketplace(voucher_id, user)

@router.get('/marketplace/user')
async def get_marketplace_user(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_auth_user)
):
    voucher_service = VoucherService(db)
    return await voucher_service.get_marketplace_user(user)

@router.get('/user_vouchers', response_model=List[UserVoucherSchema])
async def get_user_vouchers(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_auth_user)
):
    voucher_service = VoucherService(db)
    return await voucher_service.get_user_vouchers(user)

@router.get('/fast_sell/{voucher_id}', status_code=status.HTTP_204_NO_CONTENT)
async def fast_sell_voucher(
    voucher_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_auth_user)
):
    voucher_service = VoucherService(db)
    await voucher_service.fast_sell_voucher(voucher_id, user)
