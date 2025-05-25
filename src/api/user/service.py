import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import secrets
import smtplib
import struct
from fastapi import UploadFile, HTTPException, status
from api.auth.utils import hash_password
from api.task.queries import select_all_user_voucher
from api.user.crud import (
    create_user,
    get_referral_transactions,
    get_user_2fa_secret,
    get_user_by_id,
    get_user_by_username_and_password,
    get_user_email_code,
    get_user_profile,
    get_voucher_by_id,
    update_user_2fa,
    update_user_2fa_code_verified,
    update_user_2fa_code_verified_shutdown,
    update_user_2fa_secret,
    update_user_2fa_status,
    update_user_email_code,
    update_user_email_verified,
    update_user_profile, 
    get_user_by_username,
    update_user_referral,
    get_user_referrals,
)
from api.user.shemas import ReferralInfo, ReferralsList, RegisterUser, TokenInfo, UpdateUserProfile, UserSchema, UserProfile
from api.core.error import Errors
from sqlalchemy.ext.asyncio import AsyncSession
from api.auth.crt_tokens import create_token_response, ACCESS_TOKEN_TYPE, REFRESH_TOKEN_TYPE
import hashlib
import pyotp

import os



class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._secret_key = "referall".encode('utf-8')

    def _encode_referral(self, user_id: int) -> str:
        random_salt = secrets.token_bytes(8)
        data = struct.pack('>Q', user_id) + random_salt
        signature = hashlib.sha256(data + self._secret_key).digest()[:4]
        final_data = data + signature
        encoded = base64.urlsafe_b64encode(final_data).decode('ascii').rstrip('=')
        return encoded

    def _decode_referral(self, code: str) -> int:
        try:
            padding = 4 - (len(code) % 4)
            if padding != 4:
                code += '=' * padding
            
            decoded = base64.urlsafe_b64decode(code.encode('ascii'))
            
            if len(decoded) != 20:      
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Неверная длина кода"
                )
            
            user_id_bytes = decoded[:8]
            salt = decoded[8:16]
            received_signature = decoded[16:]
            
            expected_signature = hashlib.sha256(decoded[:16] + self._secret_key).digest()[:4]
            if not secrets.compare_digest(received_signature, expected_signature):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Неверная подпись"
                )
            
            user_id = struct.unpack('>Q', user_id_bytes)[0]
            return user_id
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Неверный формат реферального кода: {str(e)}"
            )

    async def generate_referral_code(self, user: UserSchema) -> str:

        return self._encode_referral(user.id)
    
    def decode_referral_code(self, referral_code: str) -> int:

        return self._decode_referral(referral_code)
    
    
    async def register_user(self, user: RegisterUser, referral_code: str | None = None) -> TokenInfo:
        hashed_password = hash_password(user.password)
        referral_id = None

        if referral_code :
            print(referral_code)
            referral_id = self.decode_referral_code(referral_code)
            print(referral_id)

        user_data = UserSchema(
            username=user.username,
            password=hashed_password,
            email=None
        )
        
        user_db = await create_user(self.db, user_data, referral_id)
        
        if user_db:
            tokens = create_token_response(user_db, [ACCESS_TOKEN_TYPE, REFRESH_TOKEN_TYPE])
            return tokens
        Errors.user_exists_exc()

    async def get_profile(self, user: UserSchema) -> UserProfile:
        user_profile = await get_user_profile(self.db, user)
        if user_profile:
            for_next_level = self.calculate_for_next_level(user_profile.level, user_profile.points)

            return UserProfile(**user_profile.__dict__, for_next_level=for_next_level)
        Errors.notfound_exc('Not found profile')

    def calculate_for_next_level(self, level: str, points: int) -> int:
        '''Подсчет очков до след уровня'''

        level_thresholds = {
            "beginner": 100,
            "intermediate": 300,
            "advanced": 600,
            "expert": 1000
        }
        return max(0, level_thresholds.get(level, 100) - points)
    
    async def update_profile(self, user: UserSchema, user_data: UpdateUserProfile) -> UserProfile:
        user_profile = await update_user_profile(self.db, user, user_data)
        if user_profile:
            return UserProfile(**user_profile.__dict__, for_next_level=self.calculate_for_next_level(user_profile.level, user_profile.points))
        Errors.notfound_exc('Not found profile')

    async def add_referral(self, user: UserSchema, referral_code: str) -> bool:
        """Добавление реферального кода к пользователю"""
        if not user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь не идентифицирован"
            )
            
        # Проверяем, что реферальный код не совпадает с username текущего пользователя
        if user.username == referral_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нельзя использовать собственный код в качестве реферального"
            )
            
        # Проверяем существование пользователя с указанным реферальным кодом
        referral_user = await get_user_by_username(self.db, referral_code)
        if not referral_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь с указанным реферальным кодом не найден"
            )
            
        result = await update_user_referral(self.db, user.id, referral_code)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Не удалось добавить реферала. Возможно, у вас уже есть реферал."
            )
            
        return True
    

    async def return_referral_bonus(self, user: UserSchema, ref_id: int):
        """Получение списка транзакций реферала"""
        if not user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь не идентифицирован"    
            )
        transactions = await get_referral_transactions(self.db, user.id, ref_id)
        bonus = 0
        for transaction in transactions:
            bonus += transaction.amount
        return bonus
    
    async def get_user_max_voucher(self, user: UserSchema):
        """Получение максимального уровня вайча"""
        all_type_voucher = {'Старт': 1, 'Базис': 2, 'Бизнес': 3, 'Премиум': 4, 'VIP': 5}
        all_type_voucher_2 = {1:'Старт', 2: 'Базис', 3: 'Бизнес', 4: 'Премиум', 5: 'VIP'}
        max_voucher = 0
        if not user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь не идентифицирован"
            )
        vouchers = await select_all_user_voucher(self.db, user.id)
        if not vouchers:
            return 0
        for voucher in vouchers:
            voucher_type = await get_voucher_by_id(self.db, voucher.voucher_id)
            if voucher_type.name in all_type_voucher:
                if all_type_voucher[voucher_type.name] > max_voucher:
                    max_voucher = all_type_voucher[voucher_type.name]
        return max_voucher

    async def on_or_off_2fa(self, user: UserSchema):
        """Включение/выключение 2FA"""
        if not user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь не идентифицирован"
            )
        user_profile = await get_user_profile(self.db, user)
        if user_profile.email_verified:
            if user_profile.FA2:
                await update_user_2fa_status(self.db, user.id, False)
            else:
                await update_user_2fa_status(self.db, user.id, True)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not verified"
            )
    async def generate_and_send_email(self, email_to: str):
        code = ''.join(secrets.choice('0123456789') for _ in range(6))
        email_from = "fondBlagoHelp@yandex.com"
        password = "ebkaeecwdrvbdfhi"

        msg = MIMEMultipart()
        msg["From"] = email_from
        msg["To"] = email_to
        msg["Subject"] = "Подтверждение по email"

        body = f"""
        Добрый день!  
        Ваш код подтверждения: {code}  
        """
        msg.attach(MIMEText(body, "plain"))

        try:
            # Попытка подключения через SSL
            with smtplib.SMTP_SSL("smtp.yandex.com", 465, timeout=10) as server:
                server.login(email_from, password)
                server.sendmail(email_from, email_to, msg.as_string())
            print("✅ Письмо отправлено!")
            return code
        except smtplib.SMTPException as e:
            print(f"❌ Ошибка SMTP: {e}")
            try:
                # Попытка подключения через TLS
                with smtplib.SMTP("77.88.21.158", 587, timeout=10) as server:
                    server.starttls()
                    server.login(email_from, password)
                    server.sendmail(email_from, email_to, msg.as_string())
                print("✅ Письмо отправлено через TLS!")
                return code
            except Exception as e:
                print(f"❌ Ошибка при попытке TLS: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Не удалось отправить письмо. Пожалуйста, попробуйте позже."
                )
        except Exception as e:
            print(f"❌ Неожиданная ошибка: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Произошла ошибка при отправке письма. Пожалуйста, попробуйте позже."
            )


    async def send_code(self, user: UserSchema):
        """Отправка кода подтверждения email"""
        if not user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь не идентифицирован"
            )
        code = await self.generate_and_send_email(user.email)
        await update_user_email_code(self.db, user.id, code)
        

    async def check_code(self, user: UserSchema, code: str):
        """Проверка кода подтверждения email"""
        if not user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь не идентифицирован"
            )
        user_code = await get_user_email_code(self.db, user.id)
        if user_code != code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not correct code"
            )
        await update_user_email_verified(self.db, user.id, True)
        return True
    
    async def check_code_2fa(self, user: UserSchema, code: str):
        if await self.check_code(user, code):
            tokens = create_token_response(user, [ACCESS_TOKEN_TYPE, REFRESH_TOKEN_TYPE])
            return tokens
        return False
    
    async def setup_google_auth(self, user: UserSchema):
        """Настройка Google Authenticator"""
        if not user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь не идентифицирован"
            )
        secret = pyotp.random_base32()
        await update_user_2fa_secret(self.db, user.id, secret)
        totp = pyotp.TOTP(secret)
    
        # 3. Генерируем URI для QR-кода
        provisioning_uri = totp.provisioning_uri(
            name=user.username,
            issuer_name="Quantex"
        )
        return provisioning_uri
    
    async def verify_google_auth(self, user: UserSchema, code: str):
        if not user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь не идентифицирован"
            )
        secret = await get_user_2fa_secret(self.db, user.id)
        totp = pyotp.TOTP(secret)
        
        return totp.verify(code)
    
    async def verify_google_auth_access(self, username: str, password: str, code: str):
        user = await get_user_by_username_and_password(self.db, username, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Неверный логин или пароль"
            )
        if await self.verify_google_auth(user, code):
            tokens = create_token_response(user, [ACCESS_TOKEN_TYPE, REFRESH_TOKEN_TYPE])
            return tokens
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный код"
        )
    
    async def verify_google_auth_setup(self, user: UserSchema, code: str):
        if await self.verify_google_auth(user, code):
            await update_user_2fa_code_verified(self.db, user.id)
            await update_user_2fa(self.db, user.id, True)
            return True
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный код"
        )
    
    async def verify_google_auth_shutdown(self, user: UserSchema, code: str):
        if not user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь не идентифицирован"
            )
        if await self.verify_google_auth(user, code):
            await update_user_2fa_code_verified_shutdown(self.db, user.id)
            await update_user_2fa(self.db, user.id, False)
            return True
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный код"
        )

        
        

    async def get_user_referrals(self, user: UserSchema):
        """Получение списка рефералов пользователя"""
        if not user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь не идентифицирован"
            )
        full_user = await get_user_by_id(self.db, user.id)
        referrals = await get_user_referrals(self.db, user.id)
        max_voucher = await self.get_user_max_voucher(user)
        referral_list = []
        active_referrals = 0
        total_volume = 0

        if max_voucher != 0:
            if max_voucher > 1:
                # Уровень 1 - прямые рефералы
                for referral in referrals:
                    bonus = await self.return_referral_bonus(user, referral.id)
                    referral_info = ReferralInfo(
                        id=referral.id,
                        logged_in_at=referral.created_at,
                        balance=bonus,
                        active=bonus > 0,
                        commission=20  # 20% для прямых рефералов
                    )
                    if bonus > 0:
                        active_referrals += 1
                    referral_list.append(referral_info)
                    total_volume += bonus

                    # Уровень 2 - рефералы рефералов
                    if max_voucher > 2:
                        level2_referrals = await get_user_referrals(self.db, referral.id)
                        for level2_referral in level2_referrals:
                            bonus = await self.return_referral_bonus(user, level2_referral.id)
                            level2_info = ReferralInfo(
                                id=level2_referral.id,
                                logged_in_at=level2_referral.created_at,
                                balance=bonus,
                                active=bonus > 0,
                                commission=15  # 15% для рефералов второго уровня
                            )
                            referral_list.append(level2_info)
                            if bonus > 0:
                                active_referrals += 1
                            total_volume += bonus

                            # Уровень 3 - рефералы рефералов рефералов
                            if max_voucher > 3:
                                level3_referrals = await get_user_referrals(self.db, level2_referral.id)
                                for level3_referral in level3_referrals:
                                    bonus = await self.return_referral_bonus(user, level3_referral.id)
                                    level3_info = ReferralInfo(
                                        id=level3_referral.id,
                                        logged_in_at=level3_referral.created_at,
                                        balance=bonus,
                                        active=bonus > 0,
                                        commission=7  # 10% для рефералов третьего уровня
                                    )
                                    referral_list.append(level3_info)
                                    if bonus > 0:
                                        active_referrals += 1
                                    total_volume += bonus

                                    # Уровень 4 - рефералы четвертого уровня
                                    if max_voucher > 4:
                                        level4_referrals = await get_user_referrals(self.db, level3_referral.id)
                                        for level4_referral in level4_referrals:
                                            bonus = await self.return_referral_bonus(user, level4_referral.id)
                                            level4_info = ReferralInfo(
                                                id=level4_referral.id,
                                                logged_in_at=level4_referral.created_at,
                                                balance=bonus,
                                                active=bonus > 0,
                                                commission=5  # 5% для рефералов четвертого уровня
                                            )
                                            referral_list.append(level4_info)
                                            if bonus > 0:
                                                active_referrals += 1
                                            total_volume += bonus

                                            # Уровень 5 - рефералы пятого уровня
                                            if max_voucher > 5:
                                                level5_referrals = await get_user_referrals(self.db, level4_referral.id)
                                                for level5_referral in level5_referrals:
                                                    bonus = await self.return_referral_bonus(user, level5_referral.id)
                                                    level5_info = ReferralInfo(
                                                        id=level5_referral.id,
                                                        logged_in_at=level5_referral.created_at,
                                                        balance=bonus,
                                                        active=bonus > 0,
                                                        commission=3  # 3% для рефералов пятого уровня
                                                    )
                                                    referral_list.append(level5_info)
                                                    if bonus > 0:
                                                        active_referrals += 1
                                                    total_volume += bonus

        referral_code = await self.generate_referral_code(user)
        return ReferralsList(
            total=len(referral_list),
            referral_code=referral_code,
            referrals=referral_list,
            active_referrals=active_referrals,
            total_volume=total_volume,
            total_active_referrals=active_referrals
        )


