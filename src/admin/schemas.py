from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class NetworkEnum(str, Enum):
    BSC = "BSC"
    ETH = "ETH"
    TON = "TON"
    BTC = "BTC"

class CurrencyEnum(str, Enum):
    USDT = "USDT"
    BNB = "BNB"
    ETH = "ETH"
    TON = "TON"
    BTC = "BTC"
    QNX = "QNX"

class ActionTypeEnum(str, Enum):
    deposit = "deposit"
    withdrawal = "withdrawal"
    exchange = "exchange"
    buy_voucher = "buy_voucher"
    create_staking = "create_staking"

class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    balance: float = 0.0
    points: int = 0
    level: str = "beginner"

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = None

class TransactionBase(BaseModel):
    user_id: int
    network: NetworkEnum
    currency: CurrencyEnum
    amount: float
    action_type: ActionTypeEnum
    status: Optional[str] = None

class VoucherBase(BaseModel):
    name: str
    cost: float
    partner_program_lines: int
    marketplace_sale: bool = False
    buyback_option: bool = False
    staking_annual_percentage: float
    copytrading_commission: float
    earn_points: bool = False
    earn_tokens: bool = False
    nft_level: Optional[str] = None
    subscription_days: int = 0

class StakingBase(BaseModel):
    min_amount: float
    max_amount: float
    percent: float
    currency: str
    network: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None 