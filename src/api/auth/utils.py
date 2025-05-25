import jwt
from datetime import timedelta, datetime, timezone
from api.core.config import settings
from api.user.shemas import UserSchema
from api.auth import utils as auth_utils
from api.core.logger.log import logger
from typing import Optional
from passlib.context import CryptContext

# Настраиваем CryptContext с явными параметрами для bcrypt
pwd_context = CryptContext(
    schemes=["bcrypt"],
    bcrypt__rounds=12,  # То же количество раундов, что и в bcrypt
    deprecated="auto"
)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    logger.info("Начало проверки пароля")
    logger.debug(f"Хеш из базы данных: {hashed_password}")
    logger.debug(f"Длина введенного пароля: {len(plain_password)}")
    logger.debug(f"Тип введенного пароля: {type(plain_password)}")
    
    try:
        # Проверяем, что хеш начинается с правильного префикса
        if not hashed_password.startswith('$2b$'):
            logger.error("Неверный формат хеша пароля")
            return False
            
        # Создаем тестовый хеш для сравнения
        test_hash = pwd_context.hash(plain_password)
        logger.debug(f"Тестовый хеш для введенного пароля: {test_hash}")
        
        # Проверяем пароль
        result = pwd_context.verify(plain_password, hashed_password)
        logger.info(f"Результат проверки пароля: {result}")
        
        # Если проверка не прошла, пробуем альтернативный метод
        if not result:
            logger.debug("Пробуем альтернативный метод проверки")
            try:
                import bcrypt
                password_bytes = plain_password.encode('utf-8')
                hashed_bytes = hashed_password.encode('utf-8')
                result = bcrypt.checkpw(password_bytes, hashed_bytes)
                logger.info(f"Результат альтернативной проверки: {result}")
            except Exception as e:
                logger.error(f"Ошибка при альтернативной проверке: {str(e)}")
        
        return result
    except Exception as e:
        logger.error(f"Ошибка при проверке пароля: {str(e)}")
        return False

def hash_password(password: str) -> str:
    try:
        hashed = pwd_context.hash(password)
        logger.debug(f"Создан новый хеш пароля: {hashed}")
        return hashed
    except Exception as e:
        logger.error(f"Ошибка при хешировании пароля: {str(e)}")
        raise

def create_access_token(
    data: dict,
    expire_timedelta: Optional[timedelta] = None,
) -> str:
    to_encode = data.copy()
    if expire_timedelta:
        expire = datetime.utcnow() + expire_timedelta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.auth_jwt.secret_key, algorithm=settings.auth_jwt.algorithm)
    return encoded_jwt

def encode_jwt(
        payload: dict,
        private_key: str = settings.auth_jwt.private_key_path.read_text(),
        algorithm: str = settings.auth_jwt.algorithm,
        expire_minutes: int = settings.auth_jwt.access_token_expire_minutes,
        expire_timedelta: timedelta | None = None,  
) -> str:
    """
    Кодирование JWT токена
    """
    logger.debug(f"Начало кодирования JWT токена для пользователя {payload.get('username')}")
    
    to_encode = payload.copy()

    now = datetime.now(timezone.utc)

    if expire_timedelta:
        expire = now + expire_timedelta
    else:
        expire = now + timedelta(minutes=expire_minutes)

    to_encode.update(
        exp=expire,
        iat=now,
    )
    
    try:
        encoded = jwt.encode(
            to_encode,
            private_key,
            algorithm=algorithm,
        )
        logger.debug(f"JWT токен успешно создан для пользователя {payload.get('username')}")
        return encoded
        
    except Exception as e:
        logger.error(f"Ошибка при создании JWT токена: {str(e)}")
        raise

def decode_jwt(
        token, 
        public_key: str = settings.auth_jwt.public_key_path.read_text(), 
        algorithm: str = settings.auth_jwt.algorithm
) -> dict:
    """
    Декодирование JWT токена
    """
    decoded = jwt.decode(
        token, 
        public_key, 
        algorithm, 
    )

    return decoded


"""тестовые пользователи""" 
john = UserSchema(
    id = 1,
    username="john_doe",
    email="john@example.com",
    password=hash_password("secret123"),
    active=True
)
sam = UserSchema(
    id = 2,
    username="jane_doe",
    email="jane@example.com",
    password=hash_password("secret456"),
    active=True
)

users = [john, sam]
""""""




    
