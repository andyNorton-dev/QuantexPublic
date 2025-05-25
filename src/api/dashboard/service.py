from typing import List

from api.dashboard.queries import select_list_transactions, select_referral_bonus, select_total_balance, select_total_points, select_win_games
from api.dashboard.shemas import DashboardModel, DashboardSortModel, HistoryModel, PointsModel, ReferralProfitModel, SortOptions, ToolsModel, TotalBalanceModel, TotalProfitModel
from db.models import TransactionPoints, User, Transaction
from sqlalchemy.ext.asyncio import AsyncSession

class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_transactions_list(self, user: User, sort: DashboardSortModel) -> List[Transaction]:
        transactions = await select_list_transactions(self.db, user, sort.sort_by)
        return transactions
    
    async def get_total_balance(self, user: User, sort: DashboardSortModel) -> List[TotalBalanceModel]:
        transactions = await select_total_balance(self.db, user, sort.sort_by)
        result = []
        last_balance = 0
        last_total = None
        
        for tx in transactions:
            last_balance += tx.balance
            if last_total is not None and last_total != 0:
                percent_change = ((last_balance - last_total) / last_total) * 100
            else:
                if last_total is None:
                    percent_change = 100
                else:
                    percent_change = 0
            print(tx.balance, 'amount')        
            result.append(TotalBalanceModel(
                balance=last_balance, 
                date=tx.date,
                percent_change=round(percent_change, 2)
            ))
            last_total = last_balance
            
        return result
    

    async def get_total_points(self, user: User, sort: DashboardSortModel) -> List[TransactionPoints]:
        return await select_total_points(self.db, user, sort.sort_by)
    
    async def get_total_profit(self, user: User, sort: DashboardSortModel) -> List[TotalProfitModel]:
        return []
    
    async def get_referral_profit(self, user: User, sort: DashboardSortModel) -> List[ReferralProfitModel]:
        transactions = await select_referral_bonus(self.db, user)
        result = []
        last_balance = 0
        last_total = None
        
        for tx in transactions:
            last_balance += tx.balance
            if last_total is not None and last_total != 0:
                percent_change = ((last_balance - last_total) / last_total) * 100
            else:
                if last_total is None:
                    percent_change = 100
                else:
                    percent_change = 0
            print(tx.balance, 'amount')        
            result.append(ReferralProfitModel(
                profit=last_balance, 
                date=tx.date,
                percent_change=round(percent_change, 2)
            ))
            last_total = last_balance
            
        return result

    async def get_tools(self, user: User) -> ToolsModel:
        win_games = await select_win_games(self.db, user)
        return ToolsModel(finance=user.balance, trading=0, games=win_games, wallet=0)
    
    async def get_balance_and_points(self, user: User, sort: DashboardSortModel):
        balance = await self.get_transactions_list(user, sort)
        points = await self.get_total_points(user, sort)
        return balance, points
    
    async def rerutn_total_points(self, user: User, sort: DashboardSortModel):
        points = await self.get_total_points(user, sort)
        list_points = []
        last_points = None
        total_points = 0
        
        for point in points:
            total_points += point.points_balance
            if last_points is not None and last_points != 0:
                percent_change = ((total_points - last_points) / last_points) * 100
            else:
                if last_points is None:
                    percent_change = 100
                else:
                    percent_change = 0
                
            list_points.append(PointsModel(
                points=total_points,
                date=point.date,
                percent_change=round(percent_change, 2)
            ))
            last_points = total_points
            
        return list_points


    async def get_dashboard(self, user: User, sort: DashboardSortModel) -> DashboardModel:
        """
        Получает данные для дашборда
        :param user: User - пользователь
        :param sort: DashboardSortModel - параметры сортировки
        :return: DashboardModel - модель данных дашборда
        """
        # Получаем транзакции и поинты
        transactions, points = await self.get_balance_and_points(user, sort)
        transactions_list = await self.get_transactions_list(user, sort)
        balance = await self.get_total_balance(user, sort)
        # # Преобразуем транзакции в модель баланса
        # total_balance = []
        # current_balance = 0
        # for tx in transactions:
        #     if hasattr(tx, 'amount'):
        #         current_balance += tx.amount
        #         total_balance.append(TotalBalanceModel(
        #             balance=current_balance,
        #             date=tx.created_at
        #         ))
        
        # Обрабатываем поинты
        total_points = []
        last_points = None
        total_points_balance = 0
        for tx in points:
            total_points_balance += tx.points_balance
            if last_points is not None and last_points != 0:
                percent_change = ((total_points_balance - last_points) / last_points) * 100
            else:
                if last_points is None:
                    percent_change = 100
                else:
                    percent_change = 0
                
            total_points.append(PointsModel(
                points=total_points_balance,
                date=tx.date,
                percent_change=round(percent_change, 2)
            ))
            last_points = total_points_balance

        # Получаем остальные данные
        total_profit = await self.get_total_profit(user, sort)
        referral_profit = await self.get_referral_profit(user, sort)
        tools = await self.get_tools(user)
        
        # Получаем историю, передавая оригинальные транзакции
        history = await self.get_history(user, points, transactions_list)

        return DashboardModel(
            total_balance=balance,  # Теперь передаем список TotalBalanceModel
            points=total_points,
            total_profit=total_profit,
            referral_profit=referral_profit,
            tools=tools,
            history=history
        )

    async def get_history(self, user: User, points: TransactionPoints, balance: Transaction) -> List[HistoryModel]:
        history = []
        
        # Добавляем транзакции баланса
        for tx in balance:
            if isinstance(tx, TotalBalanceModel):
                # Если это TotalBalanceModel, используем баланс как сумму
                history.append(HistoryModel(
                    amount=tx.balance,
                    action_type="deposit",  # или другой подходящий тип
                    action_name="balance_update",
                    date=tx.date,
                    status="completed",
                    network=tx.network,  # или получить из другого источника
                    currency=tx.currency  # или получить из другого источника
                ))
            else:
                # Если это обычная транзакция
                history.append(HistoryModel(
                    amount=tx.amount,
                    action_type=tx.action_type,
                    action_name=tx.action_type,
                    date=tx.created_at,
                    status="completed",
                    network=tx.network,
                    currency=tx.currency
                ))
        
        # Добавляем транзакции поинтов
        for tx in points:
            history.append(HistoryModel(
                amount=tx.amount,
                action_type=tx.action_type,
                action_name="points",
                date=tx.date,
                status="completed",
                network=None,
                currency=None
            ))
        
        # Сортируем все транзакции по дате (от новых к старым)
        history.sort(key=lambda x: x.date, reverse=True)
        
        return history
    

    async def get_history_for_all_time(self, user: User) -> List[HistoryModel]:
        sort = DashboardSortModel(sort_by=SortOptions.all_time)
        balance, points = await self.get_balance_and_points(user, sort)
        return await self.get_history(user, points, balance)
