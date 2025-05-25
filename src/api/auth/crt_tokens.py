# Константы
from api.core.logger.log import logger
from datetime import timedelta
from typing import List, Optional


from api.core.config import settings
from api.user.shemas import TokenInfo, UserSchema
from api.auth.utils import encode_jwt


TOKEN_TYPE_FIELD = 'type'
ACCESS_TOKEN_TYPE = 'access'
REFRESH_TOKEN_TYPE = 'refresh'

def create_jwt(
        token_type: str,
        payload: dict,
        expire_minutes: int = settings.auth_jwt.access_token_expire_minutes,
        expire_timedelta: timedelta | None = None,
) -> str:
    """
    Помогает создать JWT токен
    """
    logger.debug("Создание %s токена для пользователя %s", token_type, payload.get("username"))
    jwt_payload = {TOKEN_TYPE_FIELD: token_type}
    jwt_payload.update(payload)
    token = encode_jwt(jwt_payload, expire_minutes=expire_minutes, expire_timedelta=expire_timedelta)
    logger.info("Успешно создан %s токен для пользователя %s", token_type, payload.get("username"))
    return token

def create_access_token(
    user: UserSchema,
) -> str:
    """
    Создание access токена
    """
    logger.debug("Создание access токена для пользователя %s", user.username)
    jwt_payload = {
        "sub": str(user.id),
        "username": user.username,
        "email": user.email,
    }
    print(jwt_payload)
    token = create_jwt(
        token_type=ACCESS_TOKEN_TYPE,
        payload=jwt_payload,
        expire_minutes=settings.auth_jwt.access_token_expire_minutes,
    )
    logger.info("Access токен успешно создан для пользователя %s", user.username)
    return token
    
   
def create_refresh_token(
    user: UserSchema,
) -> str:
    """
    Создание refresh токена
    """
    logger.debug("Создание refresh токена для пользователя %s", user.username)
    jwt_payload = {
        "sub": str(user.id),
    }

    token = create_jwt(
        token_type='refresh',
        payload=jwt_payload,
        expire_timedelta=timedelta(days=settings.auth_jwt.refresh_token_expire_days),
    )
    logger.info("Refresh токен успешно создан для пользователя %s", user.username)
    return token

def create_token_response(user: UserSchema, tokens: List[str]) -> TokenInfo:
    """Создает TokenInfo с access и refresh токенами для пользователя"""

    access_token = None
    refresh_token = None    
    for token in tokens:
        if token == ACCESS_TOKEN_TYPE:
            access_token = create_access_token(user)
        elif token == REFRESH_TOKEN_TYPE:
            refresh_token = create_refresh_token(user)
    return TokenInfo(
        access_token=access_token,
        refresh_token=refresh_token,
    )