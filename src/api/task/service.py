from datetime import datetime, timedelta
from db.models import Task, User
from api.task.queries import add_in_transaction_points, add_point_bonus_inviter, check_task_done, create_multiple_tasks, create_task_done, get_task, get_voucher_by_id, select_all_tasks, select_all_user_voucher, update_daily_day, update_snake_game_points, update_three_in_row_points, update_user_points
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
import aiohttp
import hashlib
import hmac
import time

from api.task.shemas import DailyModel, GameModel
from api.core.config import settings
from api.user.crud import get_user_by_id, get_user_referrals

class TaskService:
    def __init__(self, db: AsyncSession):
        self.daile_awards = {
            1: 100,
            2: 200,
            3: 300,
            4: 400,
            5: 500,
            6: 600,
            7: 700,
        }
        self.db = db
        self.telegram_bot_token = '6439049769:AAFD3QXcWrKVNRW2BHiftgi_18P7TMHv1Z4'
        self.telegram_channel_id = -1002304905026  # Замените на ID вашего канала (должен начинаться с -100)
        self.telegram_group_id = -1001234567890  # Замените на ID вашей группы (должен начинаться с -100)
        self.telegram_bot_username = 'QuantexBot'  # Замените на имя вашего бота

    async def get_telegram_user_id(self, auth_data: str) -> int:
        """
        Получает ID пользователя Telegram из данных авторизации
        
        Args:
            auth_data: Строка с данными авторизации от Telegram
            
        Returns:
            int: ID пользователя в Telegram
            
        Raises:
            HTTPException: Если данные невалидны или не удалось получить ID
        """
        try:
            # Разбираем данные авторизации
            data = {}
            for item in auth_data.split('&'):
                key, value = item.split('=', 1)
                data[key] = value

            # Проверяем наличие необходимых полей
            required_fields = ['hash', 'auth_date', 'user']
            if not all(field in data for field in required_fields):
                raise HTTPException(status_code=400, detail="Неверный формат данных авторизации")

            # Проверяем срок действия данных (24 часа)
            auth_date = int(data['auth_date'])
            if time.time() - auth_date > 86400:
                raise HTTPException(status_code=400, detail="Данные авторизации устарели")

            # Проверяем подпись
            check_hash = data.pop('hash', '')
            data_check_string = '\n'.join(f"{k}={v}" for k, v in sorted(data.items()))
            
            # Получаем токен бота и создаем секретный ключ
            bot_token = self.telegram_bot_token
            secret_key = hmac.new(
                "WebAppData".encode(),
                bot_token.encode(),
                hashlib.sha256
            ).digest()
            
            # Проверяем подпись
            data_hash = hmac.new(
                secret_key,
                data_check_string.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if data_hash != check_hash:
                raise HTTPException(status_code=400, detail="Неверная подпись данных")

            # Извлекаем ID пользователя
            user_data = eval(data['user'])
            if not isinstance(user_data, dict) or 'id' not in user_data:
                raise HTTPException(status_code=400, detail="Неверные данные пользователя")
                
            return user_data['id']
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Ошибка при получении ID пользователя: {str(e)}")

    async def check_telegram_subscription(self, user_id: int) -> bool:
        """
        Проверяет, подписан ли пользователь на канал Telegram
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f'https://api.telegram.org/bot{self.telegram_bot_token}/getChatMember'
                params = {
                    'chat_id': self.telegram_channel_id,  # Используем ID канала вместо username
                    'user_id': user_id
                }
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('ok'):
                            status = data['result'].get('status')
                            return status in ['member', 'administrator', 'creator']
            return False
        except Exception as e:
            print(f"Ошибка при проверке подписки: {str(e)}")
            return False

    async def check_telegram_group_membership(self, user_id: int) -> bool:
        """
        Проверяет, является ли пользователь участником группы Telegram
        
        Args:
            user_id: ID пользователя в Telegram
            
        Returns:
            bool: True, если пользователь является участником группы, иначе False
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f'https://api.telegram.org/bot{self.telegram_bot_token}/getChatMember'
                params = {
                    'chat_id': self.telegram_group_id,  # Используем ID группы вместо username
                    'user_id': user_id
                }
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('ok'):
                            status = data['result'].get('status')
                            # Проверяем, что пользователь является участником группы
                            return status in ['member', 'administrator', 'creator']
            return False
        except Exception as e:
            print(f"Ошибка при проверке членства в группе: {str(e)}")
            return False

    async def check_user_voucher_on_earn_points(self, user: User) -> bool:
        user = await get_user_by_id(self.db, user.id)
        all_user_voucher = await select_all_user_voucher(self.db, user.id)
        for voucher in all_user_voucher:
            voucher = await get_voucher_by_id(self.db, voucher.voucher_id)
            if voucher.earn_points:
                return True
        return False
        
    async def get_tasks(self, user: User) -> list[Task]:
        # await create_multiple_tasks(self.db)
        tasks = await select_all_tasks(self.db, user.id)
        result = []
        for task in tasks:
            if task.main_text == "Подписаться на Telegram канал Quantex|Official":
                task.type = "validate"
                task.url = "https://t.me/quantex_io"
                task.valid = True
                if task.done:
                    task.progress = 100
                else:
                    task.progress = 0
            elif task.main_text == "Вступить в Telegram чат Quantex":
                task.type = "validate"
                task.url = "https://t.me/+RQbTRs0LyvpkYTEy"
                task.valid = True
                if task.done:
                    task.progress = 100
                else:
                    task.progress = 0
            elif task.main_text == "Изменить никнейм":
                task.type = "validate"
                task.valid = True
                if task.done:
                    task.progress = 100 
                else:
                    task.progress = 0
            elif task.main_text == "Пригласить 5 друзей по ссылке":
                task.type = "validate"
                task.valid = True
                if task.done:
                    task.progress = 100
                else:
                    task.progress = await self.select_user_ref_amount(user) * 20
            elif task.main_text == 'Набрать 10 очков в игре "3 в ряд"':
                task.type = "game"
                task.valid = True
                if task.done:
                    task.progress = 100
                else:
                    task.progress = user.three_in_row_points * 10
            # elif task.main_text == 'вступить в Telegram чат Quantex':
            #     task.type = "validate"
            #     task.valid = True
            #     task.url = "https://t.me/quantex_io"
            #     if task.done:
            #         task.progress = 100
            #     else:
            #         task.progress = 0

            elif task.main_text == 'Вступить в Telegram бота':
                task.type = "fast"
                task.valid = True
                task.url = "https://t.me/NOTBADTRIP_bot"
                if task.done:
                    task.progress = 100
                else:
                    task.progress = 0

            elif task.main_text == 'Перейти в Telegram канал Quantex, посмотреть все публикации за последние сутки и поставить реакцию на каждую из них':
                task.type = "fast"
                task.valid = True
                task.url = "https://t.me/quantex_io"
                if task.done:
                    task.progress = 100
                else:
                    task.progress = 0
            elif task.main_text == 'Набрать 10 очков в игре "змейка"':
                task.type = "game"
                task.valid = True
                if task.done:
                    task.progress = 100
                else:
                    task.progress = user.snake_game_points * 10
            else:
                task.valid = False
                if task.done:
                    task.progress = 100
                else:
                    task.progress = 0
                task.type = "fast"
            result.append(task)

        return result
    
    async def select_user_ref_amount(self, user: User) -> int:
        users = await get_user_referrals(self.db, user.id)
        return len(users)
        
    
    async def complete_task(self, task_id: int, tg_hash: str, user: User) -> None:
        task = await get_task(self.db, task_id, user.id)
        voucher = await get_voucher_by_id(self.db, user.voucher_id)

        if await check_task_done(self.db, task_id, user.id):
            raise HTTPException(status_code=400, detail="Task already done")
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
            
        if not voucher and not await self.check_user_voucher_on_earn_points(user):
            raise HTTPException(status_code=403, detail="Haven't access to earn points")
            
        # Проверка специальных условий для игр
        if task.main_text == 'Набрать 10 очков в игре "змейка"' and user.snake_game_points < 10:
            raise HTTPException(status_code=400, detail="You don't have enough points")
        elif task.main_text == 'Изминить никнейм' and user.username.lower() != 'quantex':
            raise HTTPException(status_code=400, detail="You don't have nickname 'quantex'")
        elif task.main_text == "Пригласить 5 друзей по ссылке" and await self.select_user_ref_amount(user) < 5:
            raise HTTPException(status_code=400, detail="You don't have 5 referrals")
        elif task.main_text == 'Набрать 10 очков в игре "3 в ряд"' and user.three_in_row_points < 10:
            raise HTTPException(status_code=400, detail="You don't have enough points")
        
        # elif task.main_text == "Подписываться на канал телеграм" or task.main_text == "Вступит в чат телеграм" or task.main_text == "Подписаться на канал":
        #     if not tg_hash:
        #         raise HTTPException(status_code=400, detail="No tg hash")
            
        #     # Получаем ID пользователя из хеша
        #     telegram_user_id = await self.get_telegram_user_id(tg_hash)
            
        #     # Проверяем подписку на канал или членство в группе в зависимости от задачи
        #     if task.main_text == "Подписаться на канал":
        #         is_subscribed = await self.check_telegram_subscription(telegram_user_id)
        #         if not is_subscribed:
        #             raise HTTPException(status_code=400, detail="Вы не подписаны на канал")
        #     elif task.main_text == "Вступит в чат телеграм":
        #         is_member = await self.check_telegram_group_membership(telegram_user_id)
        #         if not is_member:
        #             raise HTTPException(status_code=400, detail="Вы не являетесь участником группы")
            
        await create_task_done(self.db, task_id, user.id)
        await update_user_points(self.db, user.id, task.award)
        await add_in_transaction_points(self.db, user.id, task.award, settings.task_type.Task, task.main_text, user.points)
        await add_point_bonus_inviter(self.db, user, task.award)
    async def return_daily_tasks(self, day: int) -> DailyModel:
        result = DailyModel(day=day, all_tasks=self.daile_awards)
        return result

    async def _done_daily_task(self, user: User) -> None:
        if not await self.check_user_voucher_on_earn_points(user):
            raise HTTPException(status_code=403, detail="Haven't access to earn points")
        daily_award = self.daile_awards[user.daily_day+1]

        await update_daily_day(db=self.db, user=user, award=daily_award)
        await add_in_transaction_points(db=self.db, user_id=user.id, amount=daily_award, action_type=settings.task_type.Daily)
        await add_point_bonus_inviter(db=self.db, user=user, amount=daily_award)
        result = await self.return_daily_tasks(user.daily_day)
        return result
    
    async def check_daily_task(self, user: User) -> None:
        if user.daily_at is None:
            return await self._done_daily_task(user)
            
        if user.daily_day == 7:
            return await self.return_daily_tasks(user.daily_day)
            
        if user.daily_at + timedelta(days=1) >= datetime.now():
            return await self.return_daily_tasks(user.daily_day)
        else:
            return await self._done_daily_task(user)
            

    async def get_daily(self, user: User) -> DailyModel:
        return await self.return_daily_tasks(user.daily_day)
        
            
    async def done_game(self, game: GameModel, user: User) -> None:
        voucher = await get_voucher_by_id(self.db, user.voucher_id)
        if voucher:
            if await self.check_user_voucher_on_earn_points(user):
                if game.game_name=="snake":
                    await update_snake_game_points(self.db, user.id, game.points)
                elif game.game_name=="three_in_row":
                    await update_three_in_row_points(self.db, user.id, game.points)
                await update_user_points(self.db, user.id, game.award)
                await add_in_transaction_points(self.db, user.id, game.award, settings.task_type.Game, game.game_name)
                await add_point_bonus_inviter(self.db, user, game.award)
                return
            raise HTTPException(status_code=403, detail="Haven't access to earn points")
        raise HTTPException(status_code=403, detail="Haven't access to earn points")
    
    async def validate_task(self, user: User) -> None:
        user = await get_user_by_id(self.db, user.id)
        all_user_voucher = await select_all_user_voucher(self.db, user.id)
        all_name_voucher = []
        result = {"Квандак": False, "Биржа": False, "Империя": False}
        for user_voucher in all_user_voucher:
            voucher = await get_voucher_by_id(self.db, user_voucher.voucher_id)
            all_name_voucher.append(voucher.name)
        
        if "Базис" in all_name_voucher or "Бизнес" in all_name_voucher:
            result["Квандак"] = True
        
        if "Премиум" in all_name_voucher:
            result["Биржа"] = True
        
        if "VIP" in all_name_voucher:
            result["Империя"] = True

        return result
    
    

            

