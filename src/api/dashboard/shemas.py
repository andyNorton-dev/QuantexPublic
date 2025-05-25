from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from enum import Enum

class SortOptions(str, Enum):
    day = 24
    week =  24*7
    month = 24*30
    year = 24*365
    all_time = 10000000000000000

class DashboardSortModel(BaseModel):
    sort_by: SortOptions

class TotalBalanceModel(BaseModel):
    balance: float
    date: Optional[datetime] = None
    percent_change: float = 0.0

    class Config:
        from_attributes = True

class TotalProfitModel(BaseModel):
    profit: float
    date: datetime

    class Config:
        from_attributes = True

class PointsModel(BaseModel):
    points: int
    date: datetime
    percent_change: float = 0.0

    class Config:
        from_attributes = True

class ReferralProfitModel(BaseModel):
    profit: float
    date: datetime
    percent_change: float = 0.0

    class Config:
        from_attributes = True

class ToolsModel(BaseModel):
    finance: float
    trading: float
    games: int
    wallet: float
    id: int
    name: str
    description: str
    url: str
    action_name: Optional[str] = None
    type: str
    status: Optional[str] = None

    class Config:
        from_attributes = True

class HistoryModel(BaseModel):
    amount: float
    action_type: str
    action_name: str | None = None
    date: datetime
    status: str | None = None
    network: Optional[str] = None
    currency: Optional[str] = None
    id: int
    type: str

    class Config:
        from_attributes = True

class DashboardModel(BaseModel):
    total_balance: List[TotalBalanceModel]
    total_profit: List[TotalProfitModel]
    points: List[PointsModel]
    referral_profit: List[ReferralProfitModel]
    tools: List[ToolsModel]
    history: List[HistoryModel]

