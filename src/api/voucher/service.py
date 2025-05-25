from datetime import datetime, timedelta
from typing import List
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Market, User, UserVoucher, Voucher
from api.voucher.queries import add_bonus_to_inviter, add_transaction_to_buy_voucher, add_user_voucher, add_vouchers, create_market, delete_marketplace, delete_user_voucher, get_market_by_user_voucher_id, get_user, get_voucher_by_id, get_vouchers, select_marketplace, select_marketplace_by_id, select_marketplace_by_user_id, select_voucher_all, select_voucher_by_id, update_user_active_voucher, update_user_balance, update_user_before_buy_voucher, update_user_before_buy_voucher_marketplace, add_transaction_to_sell_voucher
from api.voucher.shemas import UserVoucherSchema, VoucherOut, Voucher as VoucherSchema
from api.indexer.queries import update_wallet_balance
from api.wallet.schemas import CryptoCurrency, NetworkType
from api.task.queries import select_all_user_voucher


class VoucherService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_vouchers(self, user: User) -> VoucherOut:
        # await add_vouchers(self.db)
        db_vouchers = await get_vouchers(self.db)
        user_active_subscription = await get_user(self.db, user.id)

        vouchers = [
            VoucherSchema(
                id=v.id,
                name=v.name,
                cost=v.cost,
                partner_program_lines=v.partner_program_lines,
                marketplace_sale=v.marketplace_sale,
                buyback_option=v.buyback_option,
                staking_annual_percentage=v.staking_annual_percentage,
                copytrading_commission=v.copytrading_commission,
                earn_points=v.earn_points,
                earn_tokens=v.earn_tokens,
                nft_level=v.nft_level,
                subscription_days=v.subscription_days
            ) 
            for v in db_vouchers
        ]

        active_subscription_name = None
        if user_active_subscription and isinstance(user_active_subscription.voucher, dict):
            active_subscription_name = user_active_subscription.voucher.get('name')
        elif user_active_subscription and hasattr(user_active_subscription.voucher, 'name'):
            active_subscription_name = user_active_subscription.voucher.name

        return VoucherOut(
            vouchers=vouchers,
            user_active_subscription=active_subscription_name
        )
    
    async def buy_voucher(self, voucher_id: int, user: User) -> None:
        voucher = await get_voucher_by_id(self.db, voucher_id)
        user = await get_user(self.db, user.id)

        if user.balance >= voucher.cost:
            
            await update_user_before_buy_voucher(self.db, user, voucher)
            await update_wallet_balance(self.db, NetworkType.ETH, user, CryptoCurrency.USDT, -voucher.cost)
            await add_transaction_to_buy_voucher(self.db, user.id, -voucher.cost)
            await add_bonus_to_inviter(self.db, user, voucher.cost)
            await add_user_voucher(self.db, user.id, voucher.id, voucher.subscription_days, voucher.cost)
            await update_user_active_voucher(self.db, user.id)
        else:
            raise HTTPException(status_code=400, detail="Недостаточно средств")
        
    def decount_days(self, user: User, voucher: Voucher) -> int:
        time_of_sub = datetime.now() - user.buy_voucher_at
        days = voucher.subscription_days - time_of_sub.days 
        return days
    
    def decount_days_user_voucher(self, user_voucher: UserVoucher) -> int:
        time_of_sub = datetime.now() - user_voucher.date
        days = user_voucher.days - time_of_sub.days 
        return days
    
    def decount_days_marketplace(self, marketplace: Market) -> int:
        time_of_sub = datetime.now() - marketplace.date
        days = marketplace.amount_days   - time_of_sub.days 
        return days
    
    async def sell_voucher(self, voucher_id: int, user: User, cost: float) -> None:
        user = await get_user(self.db, user.id)
        user_voucher = await select_voucher_by_id(self.db, voucher_id)

        if user.voucher is None:
            raise HTTPException(status_code=400, detail="Вы не имеете активную подписку")
        
        # if await select_marketplace_by_user_id(self.db, user.id) is not None:
        #     raise HTTPException(status_code=400, detail="Вы уже продаете подписку")
        
        days = self.decount_days_user_voucher(user_voucher)
        await create_market(self.db, user.id, days, cost, user_voucher.voucher_id, user_voucher.id)

    async def get_marketplace(self, user: User) -> List[VoucherSchema]:
        all_vouchers = await select_voucher_all(self.db)
        type_of_voucher = {} 
        for voucher in all_vouchers:
            type_of_voucher[voucher.id] = voucher

        markets = await select_marketplace(self.db)
        
        markets_list = []
        for market in markets:
            voucher = type_of_voucher[market.voucher_id]
            days = self.decount_days_marketplace(market)
            markets_list.append(
                VoucherSchema(
                    id=market.id,
                    name=voucher.name,
                    cost=market.cost,
                    partner_program_lines=voucher.partner_program_lines,
                    marketplace_sale=voucher.marketplace_sale,
                    buyback_option=voucher.buyback_option,
                    staking_annual_percentage=voucher.staking_annual_percentage,
                    copytrading_commission=voucher.copytrading_commission,
                    earn_points=voucher.earn_points,
                    earn_tokens=voucher.earn_tokens,
                    nft_level=voucher.nft_level,
                    subscription_days=days
                )
            )

        return markets_list
    
    async def get_marketplace_user(self, user: User) -> Market | None:
        all_vouchers = await select_voucher_all(self.db)
        type_of_voucher = {} 
        for voucher in all_vouchers:
            type_of_voucher[voucher.id] = voucher

        markets = await select_marketplace_by_user_id(self.db, user.id)
        
        markets_list = []
        for market in markets:
            # Проверяем, существует ли ваучер с таким ID в словаре
            if market.voucher_id not in type_of_voucher:
                continue  # Пропускаем рынки с несуществующими ваучерами
                
            voucher = type_of_voucher[market.voucher_id]
            days = self.decount_days_marketplace(market)
            markets_list.append(
                VoucherSchema(
                    id=voucher.id,
                    name=voucher.name,
                    cost=market.cost,
                    partner_program_lines=voucher.partner_program_lines,
                    marketplace_sale=voucher.marketplace_sale,
                    buyback_option=voucher.buyback_option,
                    staking_annual_percentage=voucher.staking_annual_percentage,
                    copytrading_commission=voucher.copytrading_commission,
                    earn_points=voucher.earn_points,
                    earn_tokens=voucher.earn_tokens,
                    nft_level=voucher.nft_level,
                    subscription_days=days
                )
            )

        return markets_list
    
    async def buy_voucher_from_marketplace(self, voucher_id: int, user: User) -> None:
        marketplace = await select_marketplace_by_id(self.db, voucher_id)
        if marketplace is None:
            raise HTTPException(status_code=400, detail="Вы не можете купить эту подписку")
        if marketplace.seller_id == user.id:
            raise HTTPException(status_code=400, detail="Вы не можете купить свою подписку")
        if user.balance >= marketplace.cost:
            seller = await get_user(self.db, marketplace.seller_id)
            days = self.decount_days_marketplace(marketplace)
            buy_voucher_at = datetime.now() - timedelta(days=days)
            voucher = await get_voucher_by_id(self.db, marketplace.voucher_id)
            await update_user_before_buy_voucher_marketplace(self.db, user, marketplace, buy_voucher_at)
            await update_user_balance(self.db, seller.id, marketplace.cost)
            await update_wallet_balance(self.db, NetworkType.ETH, user, CryptoCurrency.USDT, -marketplace.cost)
            await update_wallet_balance(self.db, NetworkType.ETH, seller, CryptoCurrency.USDT, marketplace.cost)
            await add_transaction_to_buy_voucher(self.db, user.id, -marketplace.cost)
            await add_transaction_to_sell_voucher(self.db, seller.id, marketplace.cost)
            await add_bonus_to_inviter(self.db, user, marketplace.cost)
            await delete_marketplace(self.db, marketplace.id)
            await delete_user_voucher(self.db, marketplace.user_vouchers_id)
            await add_user_voucher(self.db, user.id, voucher.id, voucher.subscription_days, marketplace.cost)
            await update_user_active_voucher(self.db, user.id)
        else:
            raise HTTPException(status_code=400, detail="Недостаточно средств")
        
    async def get_user_vouchers(self, user: User) -> List[UserVoucherSchema]:
        user_vouchers = await select_all_user_voucher(self.db, user.id)
        user_vouchers_list = []

        for user_voucher in user_vouchers:
            voucher = await get_voucher_by_id(self.db, user_voucher.voucher_id)
            market = await get_market_by_user_voucher_id(self.db, user_voucher.id)
            days_for_end = self.decount_days(user, voucher)
            if market is not None:
                market_id = market.id
            else:
                market_id = None

            
            user_vouchers_list.append(
                UserVoucherSchema(
                    id=user_voucher.id,
                    voucher_id=user_voucher.voucher_id,
                    voucher_name=voucher.name,
                    days=voucher.subscription_days,
                    days_for_end=days_for_end,
                    created_at=user_voucher.date,
                    cost=user_voucher.cost,
                    market_id=market_id
                )
            )

        return user_vouchers_list
    
    async def fast_sell_voucher(self, voucher_id: int, user: User) -> None:
        user_voucher = await select_voucher_by_id(self.db, voucher_id)
        if user_voucher is None:
            raise HTTPException(status_code=400, detail="Вы не можете продать эту подписку")
        voucher = await get_voucher_by_id(self.db, user_voucher.voucher_id)
        market = await get_market_by_user_voucher_id(self.db, user_voucher.id)
        if market is not None:
            await delete_marketplace(self.db, market.id)
        await add_transaction_to_sell_voucher(self.db, user.id, voucher.cost*0.8)
        await delete_user_voucher(self.db, user_voucher.id)
        await update_wallet_balance(self.db, NetworkType.ETH, user, CryptoCurrency.USDT, voucher.cost*0.8)
        await update_user_balance(self.db, user.id, voucher.cost*0.8)
    
    async def cancel_marketplace(self, marketplace_id: int, user: User) -> None:
        await delete_marketplace(self.db, marketplace_id)
        

