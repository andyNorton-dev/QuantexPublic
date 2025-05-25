from typing import Optional, List
from typing_extensions import Annotated
from annotated_types import MinLen, MaxLen
from fastapi import Query
from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime

class CreateUser(BaseModel):
    username: Annotated[str, MinLen(5), MaxLen(20)]
    email: Optional[EmailStr] = None

class RegisterUser(BaseModel):
    username: Annotated[str, MinLen(5), MaxLen(20)]
    password: str


class UserSchema(BaseModel):
    model_config = ConfigDict(strict=True)

    id: Optional[int] = None
    username: str
    password: str
    email: Optional[EmailStr] = None
    active: bool = True

class UserSchemaOut(BaseModel):
    id: int
    username: str
    email: Optional[EmailStr] = None
    logged_in_at: Optional[datetime] = None
    active: bool = True
    daily_day: Optional[int] = None
    daily_at: Optional[datetime] = None

    
    

class TokenInfo(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"

class UserPhotoSchema(BaseModel):
    id: Optional[int] = None
    user_id: int
    file_name: str
    file_url: str
    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    active: bool
    main_photo: Optional[UserPhotoSchema] = None

    class Config:
        from_attributes = True

class UserProfile(BaseModel):
    id: int
    username: str
    name: str | None = None
    email: Optional[EmailStr] = None
    active: bool
    phone: str | None = None
    balance: float
    points: int
    active_vouchers: int
    progress: int
    voucher: Optional[str] = None
    level: str
    FA2: bool
    for_next_level: Optional[int] = None
    referral_id: int | None = None

    class Config:
        from_attributes = True

class UpdateUserProfile(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

class ReferralAdd(BaseModel):
    referral_code: str

class ReferralUser(BaseModel):
    id: int
    username: str
    level: str
    joined_at: Optional[datetime] = None

class ReferralInfo(BaseModel):
    id: int
    logged_in_at: Optional[datetime] = None
    balance: float
    active: bool
    commission: int

class ReferralsList(BaseModel):
    total: int
    referral_code: str
    referrals: List[ReferralInfo]
    total_volume: float
    total_active_referrals: int
