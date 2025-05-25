from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class Voucher(BaseModel):
    id: int
    name: str
    cost: float
    partner_program_lines: int
    marketplace_sale: bool
    buyback_option: bool
    staking_annual_percentage: float
    copytrading_commission: float
    earn_points: bool
    earn_tokens: bool
    nft_level: Optional[str] = None
    subscription_days: int
    code: Optional[str] = None
    type: Optional[str] = None
    value: Optional[float] = None
    is_active: Optional[bool] = True
    user_id: Optional[int] = None
    user_active_subscription: Optional[str] = None

    class Config:
        from_attributes = True

class VoucherOut(BaseModel):
    vouchers: List[Voucher] = Field(default=[])
    user_active_subscription: Optional[str] = None

class UserVoucherSchema(BaseModel):
    id: int
    voucher_id: int
    voucher_name: str
    days: int
    days_for_end: int
    created_at: datetime
    cost: float
    market_id: Optional[int] = None
