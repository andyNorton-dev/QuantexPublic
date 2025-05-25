import json
from fastapi import APIRouter, Depends, File, Query, UploadFile, status, Body, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from api.auth.crt_tokens import create_token_response
from db.engine import get_db
from api.user.service import UserService
from api.user.shemas import RegisterUser, TokenInfo, UpdateUserProfile, UserProfile, UserSchema, UserSchemaOut, ReferralAdd, ReferralsList
from api.auth.validation import get_current_active_auth_user, get_current_auth_user_for_refresh, get_current_token_payload, validate_auth_user, validate_auth_user_2fa
from api.auth.crt_tokens import ACCESS_TOKEN_TYPE, REFRESH_TOKEN_TYPE
from typing import Optional
from db.models import User


router = APIRouter(prefix='/user', tags=['user'])

@router.post('/register', response_model=TokenInfo)
async def auth_user_register(
    referral_code: Optional[str] = None,
    user: RegisterUser = Depends(),
    db: AsyncSession = Depends(get_db),
) -> TokenInfo:
    user_service = UserService(db)
    return await user_service.register_user(user, referral_code)

@router.post("/login/", response_model=TokenInfo)
async def auth_user_issue_jwt( 
    user: UserSchema = Depends(validate_auth_user),
):
    tokens = create_token_response(user, [ACCESS_TOKEN_TYPE, REFRESH_TOKEN_TYPE])
    return tokens

@router.post("/refresh/", response_model=TokenInfo)
async def auth_user_refresh_jwt( 
    user: UserSchema = Depends(get_current_auth_user_for_refresh)
):
    tokens = create_token_response(user, [ACCESS_TOKEN_TYPE])
    return tokens


@router.get("/users/me/", response_model=UserSchemaOut, )
def auth_user_check_self_info(
    payload: dict = Depends(get_current_token_payload),
    user: UserSchema = Depends(get_current_active_auth_user),
):
    iat = payload.get("iat")
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "logged_in_at": iat,
    }

@router.get("/profile", response_model=UserProfile)
async def get_profile(
    user: UserSchema = Depends(get_current_active_auth_user),
    db: AsyncSession = Depends(get_db),
):
    user_service = UserService(db)
    return await user_service.get_profile(user)


@router.put("/profile/update/", response_model=UserProfile)
async def update_profile(
    user_data: UpdateUserProfile = Body(...),
    user: UserSchema = Depends(get_current_active_auth_user),
    db: AsyncSession = Depends(get_db),
):
    user_service = UserService(db)
    return await user_service.update_profile(user, user_data)

@router.get("/referrals/", response_model=ReferralsList)
async def get_user_referrals(
    user: UserSchema = Depends(get_current_active_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение списка пользователей, привлеченных по реферальной программе"""
    user_service = UserService(db)
    return await user_service.get_user_referrals(user)

@router.post("2fa/сonfirm_email/send_code", status_code=status.HTTP_204_NO_CONTENT)
async def send_code(
    user: UserSchema = Depends(get_current_active_auth_user),
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    user_service = UserService(db)
    background_tasks.add_task(user_service.send_code, user)

@router.post("2fa/сonfirm_email/check_code", status_code=status.HTTP_204_NO_CONTENT)
async def check_code(
    code: str = Body(...),
    user: UserSchema = Depends(get_current_active_auth_user),
    db: AsyncSession = Depends(get_db)
):
    user_service = UserService(db)
    return await user_service.check_code(user, code)


# @router.post("2fa/auth/send_code", status_code=status.HTTP_204_NO_CONTENT)
# async def send_code(
#     user: UserSchema = Depends(validate_auth_user_2fa),
#     db: AsyncSession = Depends(get_db)
# ):
#     user_service = UserService(db)
#     await user_service.send_code(user)


@router.post("2fa/auth/check_code", response_model=TokenInfo)
async def check_code(
    code: str = Body(...),
    user: UserSchema = Depends(validate_auth_user_2fa),
    db: AsyncSession = Depends(get_db)
):
    user_service = UserService(db)
    return await user_service.check_code_2fa(user, code)

@router.post("2fa/on_or_off_2fa", status_code=status.HTTP_204_NO_CONTENT)
async def on_or_off_2fa(
    user: UserSchema = Depends(get_current_active_auth_user),
    db: AsyncSession = Depends(get_db)
):
    user_service = UserService(db)
    await user_service.on_or_off_2fa(user)


@router.post("2fa/setup-google-auth", response_model=str)
async def setup_google_auth(
    user: UserSchema = Depends(get_current_active_auth_user),
    db: AsyncSession = Depends(get_db)
):
    user_service = UserService(db)
    return await user_service.setup_google_auth(user)

@router.post("2fa/verify-google-auth-setup", response_model=bool)
async def verify_google_auth_setup(
    code: str = Body(...),
    user: UserSchema = Depends(get_current_active_auth_user),
    db: AsyncSession = Depends(get_db)
):
    user_service = UserService(db)
    return await user_service.verify_google_auth_setup(user, code)


@router.post("2fa/verify-google-auth", response_model=TokenInfo)
async def verify_google_auth(
    username: str = Body(...),
    password: str = Body(...),
    code: str = Body(...),
    db: AsyncSession = Depends(get_db)
):
    user_service = UserService(db)
    return await user_service.verify_google_auth_access(username, password, code)


@router.post("2fa/verify-google-auth-shutdown", response_model=bool)
async def verify_google_auth_shutdown(
    user: UserSchema = Depends(get_current_active_auth_user),
    db: AsyncSession = Depends(get_db),
    code: str = Body(...),
):
    user_service = UserService(db)
    return await user_service.verify_google_auth_shutdown(user, code)


