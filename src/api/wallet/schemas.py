from pydantic import BaseModel, Field, field_validator, validator, constr, model_validator
from typing import List, Optional, Literal
from datetime import datetime
from enum import Enum



class CryptoCurrency(str, Enum):
    """Поддерживаемые криптовалюты"""
    USDT = "USDT"
    BNB = "BNB"
    ETH = "ETH"
    TON = "TON"
    BTC = "BTC"
    QNX = "QNX"

class GiveCurrency(str, Enum):
    """Поддерживаемые валюты для вывода"""
    USDT = "USDT"
    ETH = "ETH"
    TON = "TON"
    BTC = "BTC"
    QNX = "QNX"
    BNB = "BNB"

class NetworkType(str, Enum):
    """Поддерживаемые сети"""
    BSC = "BSC"
    ETH = "ETH"
    TON = "TON"
    BTC = "BTC"


class WalletBalance(BaseModel):
    """Баланс кошелька"""
    total: float = 0.0
    currency: str = "USDT"


class DepositAddress(BaseModel):
    """Адрес для пополнения"""
    currency: CryptoCurrency
    network: NetworkType
    address: str
    memo: Optional[str] = None

class ExchangeRate_and_Balance_In(BaseModel):
    currency: CryptoCurrency
    network: NetworkType
    give_currency: GiveCurrency
    give: float

    @model_validator(mode='after')
    def validate_currency(cls, values):
        network_currency_map = {
            NetworkType.BSC: [CryptoCurrency.BNB, CryptoCurrency.USDT],
            NetworkType.ETH: [CryptoCurrency.USDT, CryptoCurrency.ETH],
            NetworkType.TON: [CryptoCurrency.TON, CryptoCurrency.USDT, CryptoCurrency.QNX],
            NetworkType.BTC: [CryptoCurrency.BTC]
        }
        network = values.network
        currency = values.currency
        if network and currency not in network_currency_map.get(network, []):
            raise ValueError(f"Валюта {currency} недоступна для сети {network}")
        return values
    

class CreateDepositRequest(BaseModel):
    """Запрос на создание депозита"""
    currency: CryptoCurrency
    network: NetworkType
    amount: float = Field(..., gt=0)
    
    @field_validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Сумма должна быть больше нуля")
        return v
    
    @model_validator(mode='after')
    def validate_currency(cls, values):
        network_currency_map = {
            NetworkType.BSC: [CryptoCurrency.BNB, CryptoCurrency.USDT],
            NetworkType.ETH: [CryptoCurrency.USDT, CryptoCurrency.ETH],
            NetworkType.TON: [CryptoCurrency.TON, CryptoCurrency.USDT, CryptoCurrency.QNX],
            NetworkType.BTC: [CryptoCurrency.BTC]
        }
        network = values.network
        currency = values.currency
        if network and currency not in network_currency_map.get(network, []):
            raise ValueError(f"Валюта {currency} недоступна для сети {network}")
        return values
    
class CreateWithdrawalRequest(BaseModel):
    """Запрос на вывод средств"""
    currency: CryptoCurrency
    network: NetworkType
    amount: float = Field(..., gt=0)
    user_wallet: str
    
    @field_validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Сумма должна быть больше нуля")
        return v
    
    @model_validator(mode='after')
    def validate_currency(cls, values):
        network_currency_map = {
            NetworkType.BSC: [CryptoCurrency.BNB, CryptoCurrency.USDT],
            NetworkType.ETH: [CryptoCurrency.USDT, CryptoCurrency.ETH],
            NetworkType.TON: [CryptoCurrency.TON, CryptoCurrency.USDT, CryptoCurrency.QNX],
            NetworkType.BTC: [CryptoCurrency.BTC]
        } 
        network = values.network
        currency = values.currency
        if network and currency not in network_currency_map.get(network, []):
            raise ValueError(f"Валюта {currency} недоступна для сети {network}")
        return values


class WithdrawResponse(BaseModel):
    """Ответ на запрос о выводе средств"""
    withdraw_id: int
    currency: CryptoCurrency
    network: NetworkType
    address: str
    amount: float
    status: str | None


class TransactionListItem(BaseModel):
    """Элемент списка транзакций"""
    id: int
    action_type: str
    currency: str
    amount: float
    status: str | None
    created_at: datetime


class TransactionsList(BaseModel):
    """Список транзакций"""
    total: int
    items: List[TransactionListItem] 

class ExchangeRateModel(BaseModel):
    """Курс обмена"""
    in_usdt: float | None
    in_ton: float | None
    in_eth: float | None
    in_btc: float | None
    in_bnb: float | None
    in_qnx: float | None
    balance: float
    take: float 

class StakingModel(BaseModel):
    """Модель стейкинга"""
    id: int
    min_amount: float
    max_amount: float
    percent: float
    currency: CryptoCurrency
    network: NetworkType

class UserStakingModel(BaseModel):
    """Модель стейкинга пользователя"""
    id: int
    amount: float
    total_amount: float
    total_percent: float
    days_for_withdraw: int
    currency: str
    status: str | None


class InfoWalletModel(BaseModel):
    """Модель информации о кошельке"""
    usdt: float
    eth: float
    ton: float
    bnb: float
    btc: float
    qnx: float

class StakingBonus(BaseModel):
    """Модель бонуса стейкинга"""
    percent: float
    acsses: bool

class StakingBonusesModel(BaseModel):
    """Модель бонуса стейкинга"""
    month3: StakingBonus
    month6: StakingBonus
    month9: StakingBonus
    month12: StakingBonus


