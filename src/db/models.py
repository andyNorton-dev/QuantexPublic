from sqlalchemy import CheckConstraint, Column, Enum, Float, Integer, String, Boolean, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import declarative_base, relationship, column_property
from sqlalchemy.sql import func, select, desc

Base = declarative_base()
    

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    referral_id = Column(Integer, index=True, nullable=True)
    username = Column(String, index=True, unique=True, nullable=False)
    name = Column(String, unique=True, index=True, nullable=True)
    password = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=True)
    email_verified = Column(Boolean, default=False)
    email_code = Column(String, nullable=True)
    phone = Column(String, unique=True, nullable=True)
    FA2 = Column(Boolean, default=False)
    balance = Column(Float, default=0.0)
    points = Column(Integer, default=0)
    active_vouchers = Column(Integer, default=0)
    progress = Column(Integer, default=0)
    voucher = Column(String, nullable=True)
    level = Column(String, default='beginner')
    daily_at = Column(DateTime, default= None)
    created_at = Column(DateTime, server_default=func.now())
    daily_day = Column(Integer, default=0)
    voucher_id = Column(Integer, ForeignKey('vouchers.id', ondelete="SET NULL"), nullable=True)
    buy_voucher_at = Column(DateTime, nullable=True)
    sell_amount_voucher_days = Column(Integer, default=0)
    snake_game_points = Column(Integer, default=0)
    three_in_row_points = Column(Integer, default=0)
    fa2_code = Column(Boolean, default=False)
    fa2_secret = Column(String, nullable=True)
    
    vouchers = relationship("Voucher", back_populates="user")
    active = Column(Boolean, default=True)
    logged_in_at = Column(DateTime, nullable=True)
    wallet = relationship("Wallet", back_populates="user")
    market = relationship("Market", 
                        foreign_keys="[Market.seller_id]", 
                        back_populates="seller")
    market_buyer = relationship("Market", 
                              foreign_keys="[Market.buyer_id]", 
                              back_populates="buyer")
    staking = relationship("UserStaking", back_populates="user")

class Wallet(Base):
    __tablename__ = "wallet"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), index=True)
    ton_address = Column(String, nullable=True)
    btc_address = Column(String, nullable=True)
    eth_address = Column(String, nullable=True)
    bsc_address = Column(String, nullable=True)
    usdt_in_bsc = Column(Float, default=0.0)
    usdt_in_eth = Column(Float, default=0.0)
    usdt_in_ton = Column(Float, default=0.0)
    qnx_in_ton = Column(Float, default=0.0)
    bnb_in_bsc = Column(Float, default=0.0)
    eth_in_eth = Column(Float, default=0.0)
    ton_in_ton = Column(Float, default=0.0)
    btc_in_btc = Column(Float, default=0.0)
    last_block = Column(Integer, default=0)
    last_lt_ton = Column(BigInteger, nullable=True)
    last_hash_bsc = Column(String, nullable=True)
    ton_secret_key = Column(String, nullable=True)
    btc_secret_key = Column(String, nullable=True)
    eth_secret_key = Column(String, nullable=True)
    bsc_secret_key = Column(String, nullable=True)
    
    user = relationship("User", back_populates="wallet")

class TransactionPoints(Base):
    __tablename__ = "transaction_points"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), index=True)
    amount = Column(Float, nullable=False)
    action_type = Column(String, nullable=False)
    action_name = Column(String, nullable=True)
    points_balance = Column(Float, nullable=False)
    date = Column(DateTime, server_default=func.now())


class Transaction(Base):
    __tablename__ = "transaction_usdt"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), index=True)
    network = Column(Enum("BSC", "ETH", "TON", "BTC", name="network_enum"), nullable=False)
    currency = Column(Enum("USDT", "BNB", "ETH", "TON", "BTC", "QNX", name="currency_enum"), nullable=False)
    in_usdt = Column(Float, nullable=False)
    balance = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)
    action_type = Column(Enum("deposit", "withdrawal", "exchange", "buy_voucher", 'create_staking', 'ref_bonus', 'sell_voucher', name="action_type_enum"), nullable=False)
    user_wallet = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    status = Column(String, nullable=True)

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_type = Column(Enum("регистрация", "контент", "действие", name="task_type_enum"), nullable=False)
    difficulty = Column(Enum("легко", "средне", "сложно", name="difficulty_enum"), nullable=False)
    main_text = Column(String, nullable=False)
    additional_text = Column(String, nullable=False)
    time = Column(Integer, nullable=False)
    progress = Column(Integer, nullable=True)
    award = Column(Integer, nullable=False) # нагрда
    access = Column(Integer, nullable=False) 

    

class TaskDone(Base):
    __tablename__ = "task_done"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey('tasks.id', ondelete="CASCADE"), index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), index=True)
    date = Column(DateTime, server_default=func.now())



class Academy(Base):
    __tablename__ = "academy"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    main_heading = Column(String, nullable=False)  # большой заголовок
    additional_heading = Column(String, nullable=False)  # маленький заголовок
    avatar_url = Column(String, nullable=False)
    video_url = Column(String, nullable=True)
    text = Column(String, nullable=False)
    rating = Column(Float, CheckConstraint('rating BETWEEN 0 AND 5', name='rating_range'))
    level = Column(String, nullable=False)
    views = Column(Integer, default=0)
    time = Column(Integer, nullable=False)

class RatingAcademy(Base):
    __tablename__ = "rating_academy"

    id = Column(Integer, primary_key=True, index=True)
    academy_id = Column(Integer, ForeignKey('academy.id', ondelete="CASCADE"), index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), index=True)
    rating = Column(Integer, nullable=False)
    __table_args__ = (CheckConstraint('rating BETWEEN 1 AND 5', name='rating_range'),)


class Voucher(Base):
    __tablename__ = "vouchers"

    id = Column(Integer, primary_key=True, index=True)  # Идентификатор ваучера
    name = Column(String, nullable=False)  # Название ваучера
    cost = Column(Float, nullable=False)  # Стоимость ваучера
    partner_program_lines = Column(Integer, nullable=False)  # Линии партнерской программы
    marketplace_sale = Column(Boolean, default=False)  # Продажа на маркетплейсе
    buyback_option = Column(Boolean, default=False)  # Опция обратного выкупа
    staking_annual_percentage = Column(Float, nullable=False)  # Годовой процент стейкинга
    copytrading_commission = Column(Float, nullable=False)  # Комиссия за копитрейдинг
    earn_points = Column(Boolean, default=False)  # Возможность зарабатывать баллы
    earn_tokens = Column(Boolean, default=False)  # Возможность зарабатывать токены
    nft_level = Column(String, nullable=True)  # Уровень NFT
    subscription_days = Column(Integer, default=0)  # Количество дней подписки

    markets = relationship("Market", back_populates="voucher")
    user = relationship("User", back_populates="vouchers")

class Market(Base):
    __tablename__ = "market"

    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), index=True)
    buyer_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), index=True, nullable=True)
    voucher_id = Column(Integer, ForeignKey('vouchers.id', ondelete="CASCADE"), index=True)
    status = Column(Enum("selling", "sold", name="status_enum"), nullable=False)
    amount_days = Column(Integer, nullable=False)
    user_vouchers_id = Column(Integer, index=True, nullable=True)
    cost = Column(Float, nullable=False)
    date = Column(DateTime, server_default=func.now())

    seller = relationship("User", 
                        foreign_keys=[seller_id], 
                        back_populates="market")
    buyer = relationship("User", 
                        foreign_keys=[buyer_id], 
                        back_populates="market_buyer")
    voucher = relationship("Voucher", back_populates="markets")


class ExchangeRate(Base):
    __tablename__ = "exchange_rate"

    id = Column(Integer, primary_key=True, index=True)
    currency = Column(String, nullable=False)
    in_usdt = Column(Float, nullable=False)
    in_ton = Column(Float, nullable=False)
    in_eth = Column(Float, nullable=False)
    in_btc = Column(Float, nullable=False)
    in_bnb = Column(Float, nullable=False)
    in_qnx = Column(Float, nullable=False)
    rate = Column(Float, nullable=False)

class Staking(Base):
    __tablename__ = "staking"

    id = Column(Integer, primary_key=True, index=True)
    min_amount = Column(Float, nullable=False)
    max_amount = Column(Float, nullable=False)
    percent = Column(Float, nullable=False)
    currency = Column(String, nullable=False)
    network = Column(String, nullable=False)
    
    user_staking = relationship("UserStaking", back_populates="staking")

class UserStaking(Base):
    __tablename__ = "user_staking"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), index=True)
    staking_id = Column(Integer, ForeignKey('staking.id', ondelete="CASCADE"), index=True)
    amount = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    total_percent = Column(Float, nullable=False)
    time = Column(Integer, nullable=False)
    date = Column(DateTime, server_default=func.now())
    status = Column(String, nullable=False)

    user = relationship("User", back_populates="staking")
    staking = relationship("Staking", back_populates="user_staking")


class UserVoucher(Base):
    __tablename__ = "user_voucher"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), index=True)
    voucher_id = Column(Integer, ForeignKey('vouchers.id', ondelete="CASCADE"), index=True)
    days = Column(Integer, nullable=False)
    cost = Column(Float, nullable=False)
    date = Column(DateTime, server_default=func.now())


