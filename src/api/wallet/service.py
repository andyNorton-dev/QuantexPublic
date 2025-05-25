from typing import Dict, List, Optional, Tuple, Any
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from bitcoinlib.wallets import Wallet as BitcoinWallet
from eth_account import Account
from tonsdk.contract.wallet import Wallets, WalletVersionEnum

from db.models import ExchangeRate, Transaction
from api.user.shemas import UserSchema
from api.wallet.schemas import (
    CreateDepositRequest, CreateWithdrawalRequest, CryptoCurrency, ExchangeRate_and_Balance_In, ExchangeRateModel, InfoWalletModel, NetworkType, StakingBonus, StakingBonusesModel, TransactionListItem, UserStakingModel, GiveCurrency
)
from api.wallet.queries import create_deposit, create_exchange, create_exchange_2, create_initial_staking_options, create_staking, create_transaction_before_make_staking, create_withdrawal, fill_exchange_rates, get_all_vouchers, get_exhange_rate, get_staking, get_user_staking, get_user_wallet, create_adress, get_transactions_history, get_voucher_by_id, update_address, update_user_balance, update_wallet_balance, create_user_staking

class Wallet:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.network_currency_map = {
        NetworkType.TON: {
            CryptoCurrency.TON: 'ton_in_ton',
            CryptoCurrency.USDT: 'usdt_in_ton',
            CryptoCurrency.QNX: 'qnx_in_ton'
        },
        NetworkType.BTC: {
            CryptoCurrency.BTC: 'btc_in_btc'
        },
        NetworkType.ETH: {
            CryptoCurrency.ETH: 'eth_in_eth',
            CryptoCurrency.USDT: 'usdt_in_eth'
        },
        NetworkType.BSC: {
                CryptoCurrency.BNB: 'bnb_in_bsc',
                CryptoCurrency.USDT: 'usdt_in_bsc'
            }
        }

    def generate_wallet(self, network: NetworkType) -> str:
        import random
        import string

        def generate_random_string(length: int) -> str:
            letters = string.ascii_letters
            return ''.join(random.choice(letters) for i in range(length))

        
        if network == NetworkType.BSC:
            Account.enable_unaudited_hdwallet_features()
            account = Account.create()
            address = account.address
            private_key = account.key.hex()

            print(f"Адрес кошелька: {address}")
            print(f"Приватный ключ: {private_key}")
            return address, private_key

        elif network == NetworkType.ETH:
            Account.enable_unaudited_hdwallet_features()
            account = Account.create()
            address = account.address
            private_key = account.key.hex()

            print(f"Адрес кошелька: {address}")
            print(f"Приватный ключ: {private_key}")
            return address, private_key
        
        elif network == NetworkType.TON:
            mnemonics, pub_k, priv_k, wallet = Wallets.create(WalletVersionEnum.v4r2, workchain=0)
            wallet_address = wallet.address.to_string(True, True, False)
            private_key = priv_k.hex()
    
            return wallet_address, private_key

        elif network == NetworkType.BTC:
            wallet = BitcoinWallet.create(generate_random_string(10), network='bitcoin')
            address = wallet.get_key().address
            private_key = wallet.get_key().key_private.hex()

            print(f"Адрес кошелька: {address}")
            print(f"Приватный ключ: {private_key}")
            return address, private_key


class WalletService():
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.bonus = {3: 0.12, 6: 0.18, 9: 0.24, 12 : 0.36}
        self.network_currency_map = {
            NetworkType.TON: {
                CryptoCurrency.TON: 'ton_in_ton',
                CryptoCurrency.USDT: 'usdt_in_ton',
                CryptoCurrency.QNX: 'qnx_in_ton'
            },
            NetworkType.BTC: {
                CryptoCurrency.BTC: 'btc_in_btc'
            },
            NetworkType.ETH: {
                CryptoCurrency.ETH: 'eth_in_eth',
                CryptoCurrency.USDT: 'usdt_in_eth'
            },
            NetworkType.BSC: {
                CryptoCurrency.BNB: 'bnb_in_bsc',
                CryptoCurrency.USDT: 'usdt_in_bsc'
            }
        }

    def generate_address(self, network: NetworkType):
        wallet = Wallet(self.db)
        return wallet.generate_wallet(network)
       
    async def get_adress(self, network: NetworkType, user: UserSchema):
        user_wallet = await get_user_wallet(self.db, user)
        if user_wallet:
            network_address = {
                "TON": user_wallet.ton_address,
                "BTC": user_wallet.btc_address,
                "ETH": user_wallet.eth_address,
                "BSC": user_wallet.bsc_address
            }.get(network)

            if network_address:
                return network_address
            else:
                network_address, private_key = self.generate_address(network)
                await update_address(self.db, network, user, network_address, private_key)
                return network_address
        else:
            network_address, private_key = self.generate_address(network)
            await create_adress(self.db, network, user, network_address, private_key)
            return network_address
        
    async def deposit(self, request: CreateDepositRequest, user: UserSchema):
        await create_deposit(self.db, request, user)

    async def withdrawal(self, request: CreateWithdrawalRequest, user: UserSchema):
        user_wallet = await get_user_wallet(self.db, user)
        if user_wallet:
            user_balance = {
            "TON": {"TON": user_wallet.ton_in_ton, "USDT": user_wallet.usdt_in_eth, "QNX": user_wallet.qnx_in_ton},
            "BTC": {"BTC": user_wallet.btc_in_btc, "USDT": user_wallet.usdt_in_eth},
            "ETH": {"ETH": user_wallet.eth_in_eth, "USDT": user_wallet.usdt_in_eth},
            "BSC": {"BNB": user_wallet.bnb_in_bsc, "USDT": user_wallet.usdt_in_bsc}
        }
            if request.amount <= user_balance[request.network][request.currency] or (request.currency == CryptoCurrency.USDT and request.amount <= user_wallet.usdt_in_eth):
                if request.currency == CryptoCurrency.USDT:
                    await update_user_balance(self.db, user, -request.amount)
                    await update_wallet_balance(self.db, NetworkType.ETH, user, CryptoCurrency.USDT, request.amount)
                else:
                    await update_wallet_balance(self.db, request.network, user, request.currency, request.amount)
                await create_withdrawal(self.db, request, user)
                # if request.currency == CryptoCurrency.USDT:
                #     await update_user_balance(self.db, user, -request.amount)
            else:
                raise HTTPException(status_code=400, detail="Insufficient balance")
        else:
            raise HTTPException(status_code=400, detail="User wallet not found")

    async def transactions_history(self, user: UserSchema):
        transactions = await get_transactions_history(self.db, user)
        result = []
        for tx in transactions:
            result.append(TransactionListItem(
                id=tx.id,
                action_type=tx.action_type,
                currency=tx.currency,
                amount=tx.amount,
                status='completed',
                created_at=tx.created_at
            ))
        return result
    async def exhange_rate(self, request: ExchangeRate_and_Balance_In, user: UserSchema):
        currency = request.currency
        network = request.network
        give_currency = request.give_currency
        give = request.give
        # await fill_exchange_rates(self.db)
        result = await get_exhange_rate(self.db, currency)
        wallet_balance = await get_user_wallet(self.db, user)
        
        # Получаем имя атрибута для баланса из mapping
        balance_attr = self.network_currency_map[network][currency]
        # Получаем баланс используя getattr
        current_balance = getattr(wallet_balance, balance_attr, 0) if wallet_balance else 0
        
        # Расчет количества получаемых монет
        take_amount = 0
        if give > 0:
            # Получаем курс для валюты, которую отдаем
            give_rate_attr = f"in_{give_currency.lower()}"
            give_rate = getattr(result, give_rate_attr, 0)
            
            if give_rate > 0:
                # Рассчитываем количество получаемых монет
                # Формула: (сумма_отдаваемых * курс_отдаваемой_валюты) / курс_получаемой_валюты
                take_amount = give * give_rate
        
        return ExchangeRateModel(
            in_usdt=0 if result.in_usdt == 1.0 else result.in_usdt,
            in_ton=0 if result.in_ton == 1.0 else result.in_ton,
            in_eth=0 if result.in_eth == 1.0 else result.in_eth,
            in_bnb=0 if result.in_bnb == 1.0 else result.in_bnb,
            in_btc=0 if result.in_btc == 1.0 else result.in_btc,
            in_qnx=0 if result.in_qnx == 1.0 else result.in_qnx,
            balance=current_balance,
            take=take_amount
        )
    
    async def exchange(self, request: ExchangeRate_and_Balance_In, user: UserSchema):
        give_currency = request.currency
        give_network = request.network
        give = request.give
        take_currency = request.give_currency

        take_currency_and_network = {
            "USDT": [NetworkType.ETH, CryptoCurrency.USDT],
            "ETH": [NetworkType.ETH, CryptoCurrency.ETH],
            "BNB": [NetworkType.BSC, CryptoCurrency.BNB],
            "BTC": [NetworkType.BTC, CryptoCurrency.BTC],
            "TON": [NetworkType.TON, CryptoCurrency.TON],
            "QNX": [NetworkType.TON, CryptoCurrency.QNX]
        }[take_currency]
        user_wallet = await get_user_wallet(self.db, user)
        if not user_wallet:
            raise HTTPException(status_code=400, detail="User wallet not found")
        
        give_currency_and_network = self.network_currency_map[give_network][give_currency]
        give_balance = getattr(user_wallet, give_currency_and_network, 0)
        if give_balance < give:
            raise HTTPException(status_code=400, detail="Insufficient balance")
        
        rate = await self.exhange_rate(request, user)
        take_amount = rate.take
        if take_currency == CryptoCurrency.USDT:
            await update_user_balance(self.db, user, take_amount)
        if give_currency == CryptoCurrency.USDT:
            await update_user_balance(self.db, user, -give)
        await update_wallet_balance(self.db, give_network, user, give_currency, give)
        print(give_network, give_currency, give)
        await update_wallet_balance(self.db, take_currency_and_network[0], user, take_currency_and_network[1], -take_amount)
        print(take_currency_and_network[0], take_currency_and_network[1], take_amount)
        await create_exchange_2(self.db, request, take_amount, user, take_currency_and_network[0], take_currency_and_network[1])
        await create_exchange(self.db, request, -give, user, give_network, give_currency)
        
        result = await self.exhange_rate(request, user)
        return result
    
    async def get_info_wallet(self, user: UserSchema):
        user_wallet = await get_user_wallet(self.db, user)
        if not user_wallet:
            raise HTTPException(status_code=400, detail="User wallet not found")
        
        # Функция для проверки на NaN и преобразования в 0
        def safe_value(value):
            import math
            return 0 if value is None or (isinstance(value, float) and math.isnan(value)) else value
        
        return InfoWalletModel(
            usdt=safe_value(user_wallet.usdt_in_eth),
            eth=safe_value(user_wallet.eth_in_eth),
            ton=safe_value(user_wallet.ton_in_ton),
            bnb=safe_value(user_wallet.bnb_in_bsc),
            btc=safe_value(user_wallet.btc_in_btc),
            qnx=safe_value(user_wallet.qnx_in_ton)
        )

    async def get_exchange_rate_on_usdt(self, user: UserSchema):
        # Получаем актуальные курсы из базы данных
        # await fill_exchange_rates(self.db)
        
        # Получаем курсы для каждой валюты
        btc_rate = await get_exhange_rate(self.db, "BTC")
        eth_rate = await get_exhange_rate(self.db, "ETH")
        bnb_rate = await get_exhange_rate(self.db, "BNB")
        ton_rate = await get_exhange_rate(self.db, "TON")
        qnx_rate = await get_exhange_rate(self.db, "QNX")
        
        # Возвращаем модель с курсами относительно USDT
        return ExchangeRateModel(
            in_usdt=1.0,  # USDT к USDT всегда 1
            in_ton=ton_rate.in_usdt if ton_rate else 0,
            in_eth=eth_rate.in_usdt if eth_rate else 0,
            in_btc=btc_rate.in_usdt if btc_rate else 0,
            in_bnb=bnb_rate.in_usdt if bnb_rate else 0,
            in_qnx=qnx_rate.in_usdt if qnx_rate else 0,
            balance=0,  # Баланс не требуется для этого эндпоинта
            take=0      # Take не требуется для этого эндпоинта
        )

    async def staking(self, user: UserSchema):
        # await create_initial_staking_options(self.db)
        staking = await get_staking(self.db)
        return staking
    
    async def counting_staking(self, staking_id: int, amount: float, month: int, user: UserSchema):
        ...

    async def get_staking_bonuses(self, user: UserSchema):
        user_vouchers = await get_all_vouchers(self.db, user.id)
        max_percentage = 0
        for user_voucher in user_vouchers:
            voucher = await get_voucher_by_id(self.db, user_voucher.voucher_id)
            if voucher.staking_annual_percentage:
                max_percentage = max(max_percentage, voucher.staking_annual_percentage)
        
        if max_percentage == 0:
            return StakingBonusesModel(
                month3=StakingBonus(percent=12, acsses=False),
                month6=StakingBonus(percent=18, acsses=False),
                month9=StakingBonus(percent=24, acsses=False),
                month12=StakingBonus(percent=36, acsses=False)
            )
        elif max_percentage == 1.2 * 10:
            return StakingBonusesModel(
                month3=StakingBonus(percent=12, acsses=True),
                month6=StakingBonus(percent=18, acsses=False),
                month9=StakingBonus(percent=24, acsses=False),
                month12=StakingBonus(percent=36, acsses=False)
            )
        elif max_percentage == 1.8 * 10:
            return StakingBonusesModel(
                month3=StakingBonus(percent=12, acsses=True),
                month6=StakingBonus(percent=18, acsses=True),
                month9=StakingBonus(percent=24, acsses=False),
                month12=StakingBonus(percent=36, acsses=False)
            )
        elif max_percentage == 2.4 * 10:
            return StakingBonusesModel(
                month3=StakingBonus(percent=12, acsses=True),
                month6=StakingBonus(percent=18, acsses=True),
                month9=StakingBonus(percent=24, acsses=True),
                month12=StakingBonus(percent=36, acsses=False)
            )
        elif max_percentage == 3.6 * 10:
            return StakingBonusesModel(
                month3=StakingBonus(percent=12, acsses=True),
                month6=StakingBonus(percent=18, acsses=True),
                month9=StakingBonus(percent=24, acsses=True),
                month12=StakingBonus(percent=36, acsses=True)
            )
        else:
            return StakingBonusesModel(
                month3=StakingBonus(percent=12, acsses=False),
                month6=StakingBonus(percent=18, acsses=False),
                month9=StakingBonus(percent=24, acsses=False),
                month12=StakingBonus(percent=36, acsses=False)
            )
        
    async def create_staking(self, staking_id: int, amount: float, month: int, user: UserSchema):
        
        staking_list = await get_staking(self.db)
        
        # Находим нужный объект Staking по ID
        staking = None
        for s in staking_list:
            if s.id == staking_id:
                staking = s
                break
                
        if not staking:
            raise HTTPException(status_code=400, detail=f"Staking with ID {staking_id} not found")
        
        # Получаем кошелек пользователя
        user_wallet = await get_user_wallet(self.db, user)
        if not user_wallet:
            raise HTTPException(status_code=400, detail="User wallet not found")
        
        # Определяем, какое поле баланса нужно проверить в зависимости от валюты и сети
        balance_field = None
        if staking.currency == "USDT":
            if staking.network == "TON":
                balance_field = "usdt_in_ton"
            elif staking.network == "ETH":
                balance_field = "usdt_in_eth"
            elif staking.network == "BSC":
                balance_field = "usdt_in_bsc"
        elif staking.currency == "TON":
            balance_field = "ton_in_ton"
        elif staking.currency == "ETH":
            balance_field = "eth_in_eth"
        elif staking.currency == "BNB":
            balance_field = "bnb_in_bsc"
        elif staking.currency == "BTC":
            balance_field = "btc_in_btc"
        elif staking.currency == "QNX":
            balance_field = "qnx_in_ton"
            
        if not balance_field:
            raise HTTPException(status_code=400, detail=f"Unsupported currency or network: {staking.currency} in {staking.network}")
            
        # Проверяем, достаточно ли средств на балансе
        current_balance = getattr(user_wallet, balance_field, 0)
        if current_balance < amount:
            raise HTTPException(status_code=400, detail=f"Insufficient balance. Required: {amount}, Available: {current_balance}")
        
        if staking.min_amount <= amount <= staking.max_amount:
            if month in self.bonus:
                total_percent = self.bonus[month]
                if month == 3:
                    percent = self.bonus[3] * 0.25
                elif month == 6:
                    percent = self.bonus[6] * 0.5
                elif month == 9:
                    percent = self.bonus[9] * 0.75
                elif month == 12:
                    percent = self.bonus[12]
                
                total_amount = amount + (amount * percent)

                # Снимаем средства с баланса пользователя
                await update_wallet_balance(self.db, staking.network, user, staking.currency, amount)
                await create_transaction_before_make_staking(self.db, user.id, -amount, staking.network, staking.currency)
                if staking.currency == "USDT":
                    await update_user_balance(self.db, user, -amount)
                # Создаем запись о стейкинге
                user_staking_id = await create_user_staking(self.db, staking_id, amount, total_amount, total_percent, month, "waiting", user.id)
                return UserStakingModel(
                    id=user_staking_id,
                    amount=amount,
                    total_amount=total_amount,
                    total_percent=total_percent,
                    days_for_withdraw=month * 30,
                    currency=staking.currency,
                    status="waiting"
                )
            else:
                raise HTTPException(status_code=400, detail="Invalid staking month")
        else:
            raise HTTPException(status_code=400, detail="Invalid staking amount")
        
    async def user_staking(self, user: UserSchema):
        user_staking_list = await get_user_staking(self.db, user.id)
        if not user_staking_list:
            return []
            
        staking_list = await get_staking(self.db)
        staking_map = {s.id: s for s in staking_list}
        
        result = []
        for user_staking in user_staking_list:
            time_for_withdraw = (datetime.now() + timedelta(days=user_staking.time*30)) - datetime.now()
            days_remaining = time_for_withdraw.days
            
            staking = staking_map.get(user_staking.staking_id)
            if staking:
                result.append(UserStakingModel(
                    id=user_staking.id,
                    amount=user_staking.amount,
                    total_amount=user_staking.total_amount,
                    total_percent=user_staking.total_percent,
                    days_for_withdraw=days_remaining,
                    status=user_staking.status,
                    currency=staking.currency
                ))
        
        return result
