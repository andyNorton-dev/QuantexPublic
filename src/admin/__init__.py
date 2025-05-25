from fastapi import FastAPI
from sqladmin import Admin
from sqladmin.authentication import AuthenticationBackend
from fastapi import Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select, create_engine
from passlib.context import CryptContext
import secrets

from db.models import User, Wallet, Transaction, Task, Academy, Voucher, Market, Staking
from api.core.config import settings

# Создаем синхронный движок для sqladmin
sync_engine = create_engine(settings.database_url.replace('+asyncpg', ''))

# Генерируем безопасный ключ для сессий
SECRET_KEY = secrets.token_hex(32)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AdminAuth(AuthenticationBackend):
    def __init__(self):
        super().__init__(secret_key=SECRET_KEY)

    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        with sync_engine.connect() as conn:
            result = conn.execute(select(User).where(User.username == username))
            user = result.first()

        if not user or not pwd_context.verify(password, user.password):
            return False

        request.session.update({"token": "..."})
        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")
        if not token:
            return False
        return True

def init_admin(app: FastAPI) -> None:
    # Регистрируем модели
    from .admin_panel import (
        UserAdmin, WalletAdmin, TransactionAdmin, TaskAdmin,
        AcademyAdmin, VoucherAdmin, MarketAdmin, StakingAdmin, UserStakingAdmin
    )

    admin = Admin(
        app=app,
        engine=sync_engine,
        authentication_backend=AdminAuth(),
        title="Quantex Admin",
        base_url="/admin",
        logo_url="https://preview.redd.it/reddit-karma-2.png?width=1024&auto=webp&s=2b5b5c3c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c",
        templates_dir="templates",
    )

    admin.add_view(UserAdmin)
    admin.add_view(WalletAdmin)
    admin.add_view(TransactionAdmin)
    admin.add_view(TaskAdmin)
    admin.add_view(AcademyAdmin)
    admin.add_view(VoucherAdmin)
    admin.add_view(MarketAdmin)
    admin.add_view(StakingAdmin)
    admin.add_view(UserStakingAdmin)

__all__ = ["init_admin", "SECRET_KEY"]   