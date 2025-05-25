from sqlalchemy import  insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import ExchangeRate, Staking, User, UserStaking, UserVoucher, Voucher, Wallet, Transaction
from api.wallet.schemas import CreateDepositRequest, CreateWithdrawalRequest, CryptoCurrency, ExchangeRate_and_Balance_In, NetworkType
from api.indexer.shemas import BscIndexerModel, BscTransactionUsdt


async def get_user_wallet(db: AsyncSession, user: User):
    query = select(Wallet).where(Wallet.user_id == user.id)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def get_wallet_by_user_id(db: AsyncSession, user_id: int):
    query = select(Wallet).where(Wallet.user_id == user_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def create_adress(db: AsyncSession, network: NetworkType, user: User, address: str, private_key: str):
    if network == NetworkType.TON:
        query = insert(Wallet).values(user_id=user.id, ton_address=address, ton_secret_key=private_key)
    elif network == NetworkType.BTC:
        query = insert(Wallet).values(user_id=user.id, btc_address=address, btc_secret_key=private_key)
    elif network == NetworkType.ETH:
        query = insert(Wallet).values(user_id=user.id, eth_address=address, eth_secret_key=private_key)
    elif network == NetworkType.BSC:
        query = insert(Wallet).values(user_id=user.id, bsc_address=address, bsc_secret_key=private_key)
    await db.execute(query)
    await db.commit()

async def update_address(db: AsyncSession, network: NetworkType, user: User, address: str, private_key: str):
    if network == NetworkType.TON:
        query = update(Wallet).where(Wallet.user_id == user.id).values(ton_address=address, ton_secret_key=private_key)
    elif network == NetworkType.BTC:
        query = update(Wallet).where(Wallet.user_id == user.id).values(btc_address=address, btc_secret_key=private_key)
    elif network == NetworkType.ETH:
        query = update(Wallet).where(Wallet.user_id == user.id).values(eth_address=address, eth_secret_key=private_key)
    elif network == NetworkType.BSC:
        query = update(Wallet).where(Wallet.user_id == user.id).values(bsc_address=address, bsc_secret_key=private_key)
    await db.execute(query)
    await db.commit()

async def create_exchange(db: AsyncSession, request: ExchangeRate_and_Balance_In, give_amount: float, user: User, network: NetworkType, currency: CryptoCurrency):
    # Получаем курс валюты к USDT
    exchange_rate = await get_exhange_rate(db, request.currency)
    
    # Конвертируем сумму в USDT
    in_usdt_value = request.give * getattr(exchange_rate, "in_usdt", 1.0)
    
    query = insert(Transaction).values(
        user_id=user.id,
        network=request.network,
        currency=request.currency,
        amount=give_amount,
        action_type="exchange",
        status="success",
        in_usdt=in_usdt_value,
        balance=give_amount
    )
    await db.execute(query)
    await db.commit()


async def create_exchange_2(db: AsyncSession, request: ExchangeRate_and_Balance_In, give_amount: float, user: User, network: NetworkType, currency: CryptoCurrency):
    query = insert(Transaction).values(
        user_id=user.id,
        network=network,
        currency=currency,
        amount=give_amount,
        action_type="exchange",
        status="success",
        in_usdt=give_amount,
        balance=give_amount
    )
    await db.execute(query)
    await db.commit()

async def create_transaction_before_make_staking(db: AsyncSession, user_id: int, amount: float, network: NetworkType, currency: CryptoCurrency) -> None:
    """
    Создает запись в таблице транзакций перед созданием стейкинга
    :param db: AsyncSession - сессия базы данных
    :param user_id: int - ID пользователя
    :param amount: float - сумма транзакции
    """
    query = insert(Transaction).values(
        user_id=user_id,
        amount=amount,
        action_type='create_staking',
        status='completed',
        network=network,
        currency=currency,
        in_usdt=amount,
        balance=amount
    )
    await db.execute(query)
    await db.commit()

async def create_deposit(db: AsyncSession, request: CreateDepositRequest, user: User):
    query = insert(Transaction).values(user_id=user.id, network=request.network, currency=request.currency, amount=request.amount, action_type="deposit", status="waiting")
    await db.execute(query)
    await db.commit()

async def create_withdrawal(db: AsyncSession, request: CreateWithdrawalRequest, user: User):
    query = insert(Transaction).values(user_id=user.id, network=request.network, currency=request.currency, amount=-request.amount, action_type="withdrawal", user_wallet=request.user_wallet, status="waiting", in_usdt=request.amount, balance=request.amount)
    await db.execute(query)
    await db.commit()

async def get_transactions_history(db: AsyncSession, user: User):
    query = select(Transaction).where(Transaction.user_id == user.id).order_by(Transaction.id.desc())
    result = await db.execute(query)
    return result.scalars().all()

network_currency_map = {
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

async def update_wallet_balance(db: AsyncSession, network: NetworkType, user: User, currency: CryptoCurrency, amount: float):
    

    if network in network_currency_map and currency in network_currency_map[network]:
        column_name = network_currency_map[network][currency]
        query = update(Wallet).where(Wallet.user_id == user.id).values({column_name: getattr(Wallet, column_name) - amount})
        await db.execute(query)
        await db.commit()

async def fill_exchange_rates(db: AsyncSession) -> None:
    rates_data = [
        # USDT rates
        ExchangeRate(
            currency="USDT",
            in_usdt=1.0,
            in_ton=3.85,
            in_eth=0.00031,
            in_btc=0.000023,
            in_bnb=0.0032,
            in_qnx=21312.12,
            rate=1.0
        ),
        # BNB rates
        ExchangeRate(
            currency="BNB",
            in_usdt=311.5,
            in_ton=1198.27,
            in_eth=0.097,
            in_btc=0.0072,
            in_bnb=1.0,
            in_qnx=21312.12,
            rate=311.5
        ),
        # ETH rates
        ExchangeRate(
            currency="ETH",
            in_usdt=3214.8,
            in_ton=12377.0,
            in_eth=1.0,
            in_btc=0.0739,
            in_bnb=10.32,
            in_qnx=21312.12,
            rate=3214.8
        ),
        # TON rates
        ExchangeRate(
            currency="TON",
            in_usdt=0.26,
            in_ton=1.0,
            in_eth=0.000081,
            in_btc=0.0000059,
            in_bnb=0.00083,
            in_qnx=21312.12,
            rate=0.26
        ),
        # BTC rates
        ExchangeRate(
            currency="BTC",
            in_usdt=43500.0,
            in_ton=167475.0,
            in_eth=13.53,
            in_btc=1.0,
            in_bnb=139.65,
            in_qnx=0.112,
            rate=43500.0
        ),
        ExchangeRate(
            currency="QNX", 
            in_usdt=0.0000047,
            in_ton=0.018,
            in_eth=0.00000015,
            in_btc=0.000000011,
            in_bnb=0.000067,
            in_qnx=1.0,
            rate=0.0000047
        )
    ]

    # Очищаем существующие записи
    await db.execute(ExchangeRate.__table__.delete())
    
    # Добавляем новые записи
    for rate in rates_data:
        db.add(rate)
    
    await db.commit()

async def get_exhange_rate(db: AsyncSession, currency: CryptoCurrency):
    query = select(ExchangeRate).where(ExchangeRate.currency == currency)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def get_staking(db: AsyncSession):
    query = select(Staking)
    result = await db.execute(query)
    return result.scalars().all()

async def create_staking(db: AsyncSession, staking: Staking):
    # Преобразуем объект Staking в словарь
    staking_dict = {
        "min_amount": staking.min_amount,
        "max_amount": staking.max_amount,
        "percent": staking.percent,
        "currency": staking.currency,
        "network": staking.network
    }
    query = insert(Staking).values(staking_dict)
    await db.execute(query)
    await db.commit()

async def create_initial_staking_options(db: AsyncSession):
    """Создает три начальных варианта стейкинга"""
    staking_options = [
        {
            "min_amount": 100.0,
            "max_amount": 1000.0,
            "percent": 5.0,
            "currency": "USDT",
            "network": "ETH"
        },
        {
            "min_amount": 1000.0,
            "max_amount": 10000.0,
            "percent": 10.0,
            "currency": "TON",
            "network": "TON"
        },
        {
            "min_amount": 500.0,
            "max_amount": 5000.0,
            "percent": 7.5,
            "currency": "QNX",
            "network": "TON"
        }
    ]
    
    for option in staking_options:
        staking = Staking(**option)
        await create_staking(db, staking)
    
    return True

async def create_user_staking(db: AsyncSession, staking_id: int, amount: float, total_amount: float, total_percent: float, time: int, status: str, user_id: int):
    query = insert(UserStaking).values(staking_id=staking_id, amount=amount, total_amount=total_amount, total_percent=total_percent, time=time, status=status, user_id=user_id).returning(UserStaking.id)
    result = await db.execute(query)
    await db.commit()
    return result.scalar_one()

async def get_user_staking(db: AsyncSession, user_id: int):
    query = select(UserStaking).where(UserStaking.user_id == user_id)
    result = await db.execute(query)
    return result.scalars().all()


async def get_all_wallets_eth(db: AsyncSession):
    query = select(Wallet).where(Wallet.eth_address != None)
    result = await db.execute(query)
    wallets = []
    for wallet in result.scalars().all():
        wallets.append(wallet.eth_address)
    return wallets


async def update_user_balance(db: AsyncSession, user: User, amount: float):
    query = update(User).where(User.id == user.id).values(balance=user.balance + amount)
    await db.execute(query)
    await db.commit()

async def create_bsc_transaction_usdt(transaction: BscTransactionUsdt, user_id: int, db: AsyncSession):
    """
    Создает запись о USDT транзакции в BSC сети
    :param transaction: BscTransactionUsdt - объект транзакции
    :param user_id: int - ID пользователя
    :param db: AsyncSession - сессия базы данных
    """
    usdt_amount = float(transaction.usdt)
    query = insert(Transaction).values(
        user_id=user_id,
        network=NetworkType.BSC,
        currency=CryptoCurrency.USDT,
        amount=usdt_amount,
        in_usdt=usdt_amount,  # Для USDT значение in_usdt равно amount
        balance=usdt_amount,  # Начальный баланс равен сумме транзакции
        action_type="deposit",
        status="success"
    )
    await db.execute(query)
    await db.commit()

async def get_all_vouchers(db: AsyncSession, user_id: int):
    query = select(UserVoucher).where(UserVoucher.user_id == user_id)
    result = await db.execute(query)
    return result.scalars().all()

async def get_voucher_by_id(db: AsyncSession, voucher_id: int):
    query = select(Voucher).where(Voucher.id == voucher_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()



