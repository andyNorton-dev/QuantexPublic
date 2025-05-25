import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Optional
from fastapi import HTTPException

from api.auth.utils import hash_password, verify_password
from api.core.error import Errors
from db.engine import get_db
from db.models import Transaction, User, Voucher
from api.user.shemas import UpdateUserProfile, UserSchema, UserSchemaOut
from api.core.logger.log import logger

async def get_user_by_id(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()
    if user:
        return user

async def create_user(db: AsyncSession, user: UserSchema, referral_id: Optional[int] = None) -> User:
    logger.info(f"Начало создания пользователя {user.username}")
    logger.debug(f"Длина пароля при создании: {len(user.password)}")
    logger.debug(f"Тип пароля при создании: {type(user.password)}")
    logger.debug(f"Пароль при создании (первые 3 символа): {user.password[:3]}")
    
    # Проверяем, не является ли пароль уже хешем
    if user.password.startswith('$2b$'):
        logger.warning("Получен уже хешированный пароль, используем его как есть")
        hashed_password = user.password
    else:
        hashed_password = hash_password(user.password)
        logger.debug(f"Создан новый хеш пароля: {hashed_password}")
    
    try:
        # Проверяем существование пользователя перед созданием
        existing_user = await check_user_exists(db, user)
        if existing_user:
            logger.warning(f"Пользователь с именем {user.username} уже существует")
            return None

        db_user = User(
            username=user.username,
            email=user.email,
            password=hashed_password,
            referral_id=referral_id,
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        logger.info(f"Успешно создан новый пользователь: {user.username}")
        return db_user
    except Exception as e:
        await db.rollback()
        logger.error(f"Ошибка при создании пользователя {user.username}: {str(e)}")
        raise

async def check_user_exists(db: AsyncSession, user: UserSchema):
    result = await db.execute(select(User).filter(
        (User.username == user.username)
    ))
    return result.scalars().first()

async def get_user_by_username_and_password(db: AsyncSession, username: str, password: str):
    # Сначала получаем пользователя только по имени пользователя
    result = await db.execute(select(User).filter(User.username == username))
    user = result.scalars().first()
    
    logger.info(f"Попытка аутентификации пользователя {username}")
    
    if not user:
        logger.warning(f"Пользователь {username} не найден")
        return None
    
    logger.debug(f"Найден пользователь в базе данных: {user.username}")
    logger.debug(f"Хеш пароля в базе данных: {user.password}")
    logger.debug(f"Длина введенного пароля: {len(password)}")
    logger.debug(f"Тип введенного пароля: {type(password)}")
    logger.debug(f"Введенный пароль (первые 3 символа): {password[:3]}")
    
    # Если пользователь найден, проверяем пароль
    try:
        is_valid = verify_password(password, user.password)
        logger.info(f"Результат проверки пароля для пользователя {username}: {is_valid}")
        
        if is_valid:
            logger.info(f"Пользователь {username} успешно аутентифицирован")
            return user
        
        logger.warning(f"Неверный пароль для пользователя {username}")
        return None
    except Exception as e:
        logger.error(f"Ошибка при проверке пароля: {str(e)}")
        return None

async def get_user_profile(db: AsyncSession, user: UserSchema):
    result = await db.execute(select(User).filter(
        (User.username == user.username)
    ))
    return result.scalars().first()

async def update_user_profile(db: AsyncSession, user: UserSchema, user_data: UpdateUserProfile):
    update_values = {}
    if user_data.name is not None:
        # Проверяем, что имя не пустое
        if user_data.name.strip() == '':
            raise HTTPException(status_code=400, detail='Name cannot be empty')
        # Проверяем, не используется ли имя другим пользователем
        existing_user = await db.execute(
            select(User).filter(User.name == user_data.name, User.id != user.id)
        )
        if existing_user.scalars().first():
            raise HTTPException(status_code=400, detail='Name already exists')
        update_values['name'] = user_data.name
    if user_data.email is not None:
        # Проверяем, не используется ли email другим пользователем
        existing_user = await db.execute(
            select(User).filter(User.email == user_data.email, User.id != user.id)
        )
        if existing_user.scalars().first():
            raise HTTPException(status_code=400, detail='Email already exists')
        update_values['email'] = user_data.email
    if user_data.phone is not None:
        update_values['phone'] = user_data.phone

    if update_values:
        await db.execute(update(User).filter(
            User.id == user.id
        ).values(update_values))
        await db.commit()

        updated_user = await db.execute(select(User).filter(User.id == user.id))
        updated_user = updated_user.scalars().first()
        if updated_user:
            return updated_user
        else:
            Errors.notfound_exc('Not found profile')

async def get_user_by_username(db: AsyncSession, username: str):
    """Получение пользователя по имени пользователя"""
    result = await db.execute(select(User).filter(User.username == username))
    return result.scalars().first()

async def update_user_referral(db: AsyncSession, user_id: int, referral_code: str) -> bool:
    """Обновление реферального кода пользователя"""
    try:
        # Получаем ID реферала по username
        referral_user = await get_user_by_username(db, referral_code)
        if not referral_user:
            return False
            
        # Проверяем, что пользователь не пытается указать себя в качестве реферала
        if referral_user.id == user_id:
            return False
            
        # Получаем текущего пользователя
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalars().first()
        if not user:
            return False
            
        # Проверяем, что у пользователя еще нет реферала
        if user.referral_id is not None:
            return False
            
        # Обновляем реферальный ID
        user.referral_id = referral_user.id
        await db.commit()
        return True
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Ошибка при обновлении реферала для пользователя {user_id}: {str(e)}")
        return False

async def get_user_referrals(db: AsyncSession, user_id: int):
    """Получение списка пользователей, привлеченных текущим пользователем"""
    try:
        result = await db.execute(select(User).filter(User.referral_id == user_id))
        referrals = result.scalars().all()
        return referrals
    except Exception as e:
        logger.error(f"Ошибка при получении списка рефералов пользователя {user_id}: {str(e)}")
        return []
    

async def get_voucher_by_id(db: AsyncSession, voucher_id: int):
    result = await db.execute(select(Voucher).filter(Voucher.id == voucher_id))
    voucher = result.scalars().first()
    return voucher

async def get_referral_transactions(db: AsyncSession, user_id: int, ref_id: int):
    result = await db.execute(select(Transaction).filter(Transaction.user_id == user_id, Transaction.user_wallet == str(ref_id)))
    transactions = result.scalars().all()
    return transactions

async def get_user_2fa_status(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()
    return user.FA2

async def update_user_2fa_status(db: AsyncSession, user_id: int, status: bool):
    await db.execute(update(User).filter(User.id == user_id).values(FA2=status))
    await db.commit()

async def update_user_email_code(db: AsyncSession, user_id: int, code: str):
    await db.execute(update(User).filter(User.id == user_id).values(email_code=code))
    await db.commit()

async def get_user_email_code(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()
    return user.email_code

async def update_user_email_verified(db: AsyncSession, user_id: int, verified: bool):
    await db.execute(update(User).filter(User.id == user_id).values(email_verified=verified))
    await db.commit()

async def update_user_2fa_secret(db: AsyncSession, user_id: int, secret: str):
    """Обновление секретного ключа 2FA"""
    await db.execute(update(User).filter(User.id == user_id).values(fa2_secret=secret))
    await db.commit()

async def get_user_2fa_secret(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()
    return user.fa2_secret



async def update_user_2fa(db: AsyncSession, user_id: int, status: bool):
    await db.execute(update(User).filter(User.id == user_id).values(FA2=status))
    await db.commit()

async def update_user_2fa_code_verified_shutdown(db: AsyncSession, user_id: int):
    await db.execute(update(User).filter(User.id == user_id).values(fa2_code=False))
    await db.commit()

async def update_user_2fa_code_verified(db: AsyncSession, user_id: int):
    await db.execute(update(User).filter(User.id == user_id).values(fa2_code=True))
    await db.commit()














