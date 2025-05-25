from sqladmin import ModelView

from db.models import User, UserStaking, Wallet, Transaction, Task, Academy, Voucher, Market, Staking

class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.username, User.email, User.balance, User.points, User.level]
    column_searchable_list = [User.username, User.email]
    column_sortable_list = [User.id, User.balance, User.points]
    column_default_sort = ("id", True)
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    name = "Пользователь"
    name_plural = "Пользователи"
    icon = "fa-solid fa-users"

class WalletAdmin(ModelView, model=Wallet):
    column_list = [Wallet.id, Wallet.user_id, Wallet.ton_address, Wallet.btc_address, Wallet.eth_address, Wallet.bsc_address]
    column_searchable_list = [Wallet.ton_address, Wallet.btc_address, Wallet.eth_address, Wallet.bsc_address]
    column_sortable_list = [Wallet.id, Wallet.user_id]
    column_default_sort = ("id", True)
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    name = "Кошелек"
    name_plural = "Кошельки"
    icon = "fa-solid fa-wallet"

class TransactionAdmin(ModelView, model=Transaction):
    column_list = [Transaction.id, Transaction.user_id, Transaction.network, Transaction.currency, Transaction.amount, Transaction.status, Transaction.action_type]
    column_searchable_list = [Transaction.user_id]
    column_sortable_list = [Transaction.id, Transaction.amount]
    column_default_sort = ("id", True)
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    name = "Транзакция"
    name_plural = "Транзакции"
    icon = "fa-solid fa-money-bill-transfer"

class TaskAdmin(ModelView, model=Task):
    column_list = [Task.id, Task.task_type, Task.difficulty, Task.main_text, Task.award]
    column_searchable_list = [Task.main_text]
    column_sortable_list = [Task.id, Task.award]
    column_default_sort = ("id", True)
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    name = "Задача"
    name_plural = "Задачи"
    icon = "fa-solid fa-tasks"

class AcademyAdmin(ModelView, model=Academy):
    column_list = [Academy.id, Academy.type, Academy.topic, Academy.main_heading, Academy.rating, Academy.level]
    column_searchable_list = [Academy.topic, Academy.main_heading]
    column_sortable_list = [Academy.id, Academy.rating]
    column_default_sort = ("id", True)
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    name = "Академия"
    name_plural = "Академия"
    icon = "fa-solid fa-graduation-cap"

class VoucherAdmin(ModelView, model=Voucher):
    column_list = [Voucher.id, Voucher.name, Voucher.cost, Voucher.partner_program_lines, Voucher.staking_annual_percentage]
    column_searchable_list = [Voucher.name]
    column_sortable_list = [Voucher.id, Voucher.cost]
    column_default_sort = ("id", True)
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    name = "Ваучер"
    name_plural = "Ваучеры"
    icon = "fa-solid fa-ticket"

class MarketAdmin(ModelView, model=Market):
    column_list = [Market.id, Market.seller_id, Market.buyer_id, Market.voucher_id, Market.status, Market.cost]
    column_searchable_list = [Market.seller_id, Market.buyer_id]
    column_sortable_list = [Market.id, Market.cost]
    column_default_sort = ("id", True)
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    name = "Маркет"
    name_plural = "Маркет"
    icon = "fa-solid fa-store"

class StakingAdmin(ModelView, model=Staking):
    column_list = [Staking.id, Staking.min_amount, Staking.max_amount, Staking.percent, Staking.currency, Staking.network]
    column_searchable_list = [Staking.currency, Staking.network]
    column_sortable_list = [Staking.id, Staking.percent]
    column_default_sort = ("id", True)
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    name = "Стейкинг"
    name_plural = "Стейкинг"
    icon = "fa-solid fa-percentage" 

class UserStakingAdmin(ModelView, model=UserStaking):
    column_list = [UserStaking.id, UserStaking.user_id, UserStaking.staking_id, UserStaking.amount, UserStaking.status]
    column_searchable_list = [UserStaking.user_id, UserStaking.staking_id]
    column_sortable_list = [UserStaking.id, UserStaking.amount]
    column_default_sort = ("id", True)
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    name = "Стейкинг пользователя"
    name_plural = "Стейкинг пользователей"
    icon = "fa-solid fa-clock"