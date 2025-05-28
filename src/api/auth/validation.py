from fastapi import Depends, Form, HTTPException, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from typing_extensions import Annotated

from api.auth.utils import hash_password
from api.auth.crt_tokens import ACCESS_TOKEN_TYPE, REFRESH_TOKEN_TYPE, TOKEN_TYPE_FIELD
from api.core.error import Errors
from api.user.crud import check_user_exists, get_user_by_id, get_user_by_username_and_password
from api.user.shemas import UserSchema
from api.auth import utils as auth_utils
from api.core.logger.log import logger
from db.engine import get_db
from api.user.service import UserService

http_bearer = HTTPBearer()
async def validate_auth_user(
        username: str = Body(...),
        password: str = Body(...),
        db: AsyncSession = Depends(get_db),
) -> UserSchema:
    """
    Проверка пользователя на наличие в списке пользователей
    """
    logger.info("Начало процесса аутентификации")
    logger.info(f"Попытка аутентификации пользователя: {username}")
    logger.debug(f"Полученные данные - username: {username}, password: {'*' * len(password)}")
    
    # Не хешируем пароль здесь, это будет сделано в get_user_by_username_and_password
    user_exists = await get_user_by_username_and_password(db, username, password)
    
    if user_exists:
        logger.info(f"Пользователь {username} найден в базе данных")
        if user_exists.fa2_code:
            logger.info(f"Пользователь {username} требует 2FA Google Authenticator")
            raise HTTPException(status_code=403, detail="2FA Google Authenticator is required")
        if user_exists.FA2:
            logger.info(f"Пользователь {username} требует 2FA")
            user_service = UserService(db)
            await user_service.send_code(user_exists)
            raise HTTPException(status_code=403, detail="2FA is required")
        logger.info(f"Пользователь {username} успешно аутентифицирован")
        return user_exists
            
    logger.warning(f"Неудачная попытка аутентификации для пользователя: {username}")
    Errors.unauthed_exc()

async def validate_auth_user_2fa(
    username: str = Form(),
    password: str = Form(),
    db: AsyncSession = Depends(get_db)
) -> UserSchema:
    """
    Проверка пользователя на наличие в списке пользователей
    """
    logger.info("Попытка аутентификации пользователя: %s", username)
    
    # Не хешируем пароль здесь, это будет сделано в get_user_by_username_and_password
    user_exists = await get_user_by_username_and_password(db, username, password)
    if user_exists:
        logger.info("Пользователь %s успешно аутентифицирован", username)
        return user_exists
            
    logger.warning("Неудачная попытка аутентификации для пользователя: %s", username)
    Errors.unauthed_exc()

def get_current_token_payload(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
) -> dict:
    """
    Получение payload из JWT токена
    """
    token = credentials.credentials
    logger.debug("Попытка декодирования JWT токена: %s", token[:10] + "...")
    try:
        payload = auth_utils.decode_jwt(
            token=token,
        )
        logger.debug("Декодированный payload: %s", payload)
        logger.info("JWT токен успешно декодирован")
    except jwt.ExpiredSignatureError:
        logger.warning("Срок действия токена истек")
        Errors.token_expired_exc()
    except jwt.InvalidTokenError as e:
        logger.warning("Ошибка валидации токена: %s", str(e))
        Errors.invalid_token_exc(e)
    return payload

def validate_token_type(
    payload: dict,
    token_type: str,
) -> bool:
    """
    Проверка типа токена
    """
    current_token_type = payload.get(TOKEN_TYPE_FIELD)
    if current_token_type != token_type:
        Errors.invalid_token_exc(f'token {current_token_type!r}, expected {token_type!r} token')
    return True

async def get_user_by_token_sub(
    payload: dict,
    db: AsyncSession = Depends(get_db)
) -> UserSchema:
    """
    Получение пользователя по sub из payload
    """
    userid: str | None = payload.get("sub")
    print(userid)
    user = await get_user_by_id(db, int(userid))
        
    if user:
        return user
    Errors.user_not_found_exc()


    
class UserGetterFromToken:
    """
    Получение пользователя из токена
    """
    def __init__(self, token_type: str):
        self.token_type = token_type

    async def __call__(
        self,
        payload: dict = Depends(get_current_token_payload),
        db: AsyncSession = Depends(get_db)
    ):
        validate_token_type(payload, self.token_type)
        return await get_user_by_token_sub(payload, db)
    
get_current_auth_user_for_refresh = UserGetterFromToken(REFRESH_TOKEN_TYPE)
get_current_auth_user = UserGetterFromToken(ACCESS_TOKEN_TYPE)


            

async def get_current_active_auth_user(
    current_user: Annotated[UserSchema, Depends(get_current_auth_user)],
    db: AsyncSession = Depends(get_db)
) -> UserSchema:
    """
    Получение текущего активного пользователя
    """
    user = await get_user_by_id(db, current_user.id)
    if user.active:
        logger.info("Пользователь %s активен", current_user.username)
        return user
    logger.warning("Пользователь %s неактивен", current_user.username)
    Errors.inactive_user_exc()