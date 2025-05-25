from datetime import datetime
from typing import List

from sqlalchemy import select, update, insert, delete
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Market, Transaction, User, UserVoucher, Voucher, Wallet
from api.wallet.schemas import CryptoCurrency, NetworkType


async def get_vouchers(db: AsyncSession) -> List[Voucher]:
    result = await db.execute(select(Voucher))
    return result.scalars().all()


async def get_user(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalars().first()

async def get_voucher_by_id(db: AsyncSession, voucher_id: int) -> Voucher | None:
    result = await db.execute(select(Voucher).where(Voucher.id == voucher_id))
    return result.scalars().first()

async def update_user_voucher(db: AsyncSession, user_id: int, voucher_id: int, voucher_name: str) -> None:
    query = update(User).where(User.id == user_id).values(voucher_id=voucher_id, voucher=voucher_name, buy_voucher_at=datetime.now(), sell_amount_voucher_days=0)
    await db.execute(query)
    await db.commit()

async def update_user_before_buy_voucher(db: AsyncSession, user: User, voucher:Voucher) -> None:
    query = update(User).where(User.id == user.id).values(balance=user.balance - voucher.cost, voucher_id=voucher.id, voucher=voucher.name, buy_voucher_at=datetime.now(), sell_amount_voucher_days=0)
    await db.execute(query)
    await db.commit()

async def update_user_before_buy_voucher_marketplace(db: AsyncSession, user: User, marketplace: Market, buy_voucher_at: datetime) -> None:
    query = update(User).where(User.id == user.id).values(balance=user.balance - marketplace.cost, voucher_id=marketplace.voucher_id, voucher=marketplace.voucher.name, buy_voucher_at=buy_voucher_at)
    await db.execute(query)
    await db.commit()

async def create_market(db: AsyncSession, seller_id: int, amount_days: int, cost: float, voucher_id: int, user_vouchers_id: int) -> None:
    market = Market(seller_id=seller_id, status="selling", amount_days=amount_days, cost=cost, voucher_id=voucher_id, user_vouchers_id=user_vouchers_id)
    db.add(market)
    await db.commit()
    await db.refresh(market)
    return market

async def get_market(db: AsyncSession, market_id: int) -> Market | None:
    result = await db.execute(select(Market).where(Market.id == market_id))
    return result.scalars().first()

async def update_market(db: AsyncSession, market_id: int, buyer_id: int) -> None:
    query = update(Market).where(Market.id == market_id).values(buyer_id=buyer_id, status="sold")
    await db.execute(query)
    await db.commit()

async def add_transaction_to_sell_voucher(db: AsyncSession, user_id: int, amount: float):
    query = insert(Transaction).values(user_id=user_id, network="ETH", currency="USDT", amount=amount, action_type="sell_voucher", in_usdt=amount, balance=amount, status="success")
    await db.execute(query)
    await db.commit()

async def select_marketplace(db: AsyncSession) -> List[Market]:
    result = await db.execute(select(Market))
    markets = result.scalars().all()        
    return markets

async def select_marketplace_by_user_id(db: AsyncSession, user_id: int) -> List[Market]:
    result = await db.execute(select(Market).where(Market.seller_id == user_id, Market.status == "selling"))
    market = result.scalars().all()
    return market

async def select_voucher_all(db: AsyncSession) -> List[Voucher]:
    result = await db.execute(select(Voucher))
    return result.scalars().all()

async def add_transaction_to_buy_voucher(db: AsyncSession, user_id: int, amount: float) -> None:
    query = insert(Transaction).values(user_id=user_id, amount=amount, action_type='buy_voucher', status='completed', network=NetworkType.ETH, currency=CryptoCurrency.USDT, in_usdt=amount, balance = 0)
    await db.execute(query)
    await db.commit()


async def get_user_inviter(db: AsyncSession, user: User) -> User | None:
    result = await db.execute(select(User).where(User.id == user.referral_id))
    return result.scalars().first()

async def get_user_inviters(db: AsyncSession, user: User) -> List[User]:
    inviters = {}
    for line in range(5):
        user = await get_user_inviter(db, user)
        if user is not None:
            voucher = await get_voucher_by_id(db, user.voucher_id)
            if voucher.partner_program_lines >= line + 1:
                inviters[user.id] = [True, user.balance]
            else:
                inviters[user.id] = [False, user.balance]
        else:
            break
    return inviters

async def add_transaction_to_inviter(db: AsyncSession, user: User, amount: float, ref_id: int) -> None:
    query = insert(Transaction).values(user_id=user.id, amount=amount, action_type='ref_bonus', status='completed', network=NetworkType.ETH, currency=CryptoCurrency.USDT, in_usdt=amount, balance = 0, user_wallet=str(ref_id))
    await db.execute(query)
    await db.commit()

async def update_usdt_wallet_inviter(db: AsyncSession, user: User, amount: float) -> None:
    query = update(Wallet).where(Wallet.user_id == user.id).values(usdt_in_eth= Wallet.usdt_in_eth + amount)
    await db.execute(query)
    await db.commit()

async def add_bonus_to_inviter(db: AsyncSession, user: User, amount: float) -> None:
    bonus_perhaps = {
        1: 0.2,
        2: 0.15,
        3: 0.07,
        4: 0.05,
        5: 0.03
    }
    inviters = await get_user_inviters(db, user)
    line = 0    
    for inviter_id in inviters:
        if inviters[inviter_id][0]:
            line += 1
            bonus = amount * bonus_perhaps[line]    
            query = update(User).where(User.id == inviter_id).values(balance=inviters[inviter_id][1] + bonus)
            await add_transaction_to_inviter(db, await get_user(db, inviter_id), bonus, user.id)
            await update_usdt_wallet_inviter(db, await get_user(db, inviter_id), bonus)
            await db.execute(query)
            await db.commit()


async def select_marketplace_by_id(db: AsyncSession, voucher_id: int) -> Market | None:
    result = await db.execute(select(Market).where(Market.id == voucher_id))
    return result.scalars().first()

async def delete_marketplace(db: AsyncSession, market_id: int) -> None:
    query = delete(Market).where(Market.id == market_id)
    await db.execute(query)
    await db.commit()


async def add_user_voucher(db: AsyncSession, user_id: int, voucher_id: int, days: int, cost: float) -> None:
    query = insert(UserVoucher).values(user_id=user_id, voucher_id=voucher_id, days=days, cost=cost)
    await db.execute(query)
    await db.commit()


async def update_user_active_voucher(db: AsyncSession, user_id: int) -> None:
    query = update(User).where(User.id == user_id).values(active_vouchers=User.active_vouchers + 1)
    await db.execute(query)
    await db.commit()

async def select_voucher_by_id(db: AsyncSession, voucher_id: int) -> Voucher | None:
    result = await db.execute(select(UserVoucher).where(UserVoucher.id == voucher_id))
    return result.scalars().first()

async def delete_user_voucher(db: AsyncSession, user_voucher_id: int) -> None:
    query = delete(UserVoucher).where(UserVoucher.id == user_voucher_id)
    await db.execute(query)
    await db.commit()

async def update_user_balance(db: AsyncSession, user_id: int, amount: float) -> None:
    query = update(User).where(User.id == user_id).values(balance=User.balance + amount)
    await db.execute(query)
    await db.commit()

async def get_market_by_user_voucher_id(db: AsyncSession, user_voucher_id: int) -> Market | None:
    result = await db.execute(select(Market).where(Market.user_vouchers_id == user_voucher_id))
    return result.scalars().first()

from sqlalchemy import insert

async def add_vouchers(db: AsyncSession):
    vouchers = [
        {
            "name": "Старт",
            "cost": 0.0,
            "partner_program_lines": 0,
            "marketplace_sale": False,
            "buyback_option": False,
            "staking_annual_percentage": 0.0,
            "copytrading_commission": 0.0,
            "earn_points": True,
            "earn_tokens": False,
            "nft_level": None,
            "subscription_days": 30
        },
        {
            "name": "Базис",
            "cost": 29.0,
            "partner_program_lines": 2,
            "marketplace_sale": True,
            "buyback_option": False,
            "staking_annual_percentage": 12.0,
            "copytrading_commission": 30.0,
            "earn_points": True,
            "earn_tokens": False,
            "nft_level": None,
            "subscription_days": 30
        },
        {
            "name": "Бизнес",
            "cost": 49.0,
            "partner_program_lines": 3,
            "marketplace_sale": True,
            "buyback_option": False,
            "staking_annual_percentage": 18.0,
            "copytrading_commission": 30.0,
            "earn_points": True,
            "earn_tokens": True,
            "nft_level": "бронзовый",    
            "subscription_days": 30
        },
        {
            "name": "Премиум",
            "cost": 65.0,
            "partner_program_lines": 4,
            "marketplace_sale": True,
            "buyback_option": True,
            "staking_annual_percentage": 24.0,
            "copytrading_commission": 20.0,
            "earn_points": True,
            "earn_tokens": True,
            "nft_level": "серебренный",
            "subscription_days": 30
        },
        {
            "name": "VIP",
            "cost": 100.0,
            "partner_program_lines": 5,
            "marketplace_sale": True,
            "buyback_option": True,
            "staking_annual_percentage": 36.0,
            "copytrading_commission": 20.0,
            "earn_points": True,
            "earn_tokens": True,
            "nft_level": "золотой",
            "subscription_days": 30
        }
    ]

    for voucher in vouchers:
        query = insert(Voucher).values(**voucher)
        await db.execute(query)
    await db.commit()


