import asyncio
from fastapi import FastAPI
from api.academy.queries import create_multiple_academy
from api.user.route import router as user_router
from api.voucher.queries import add_vouchers
from api.wallet.queries import create_initial_staking_options
from api.wallet.router import router as wallet_router
from api.academy.router import router as academy_router
from api.task.router import router as task_router
from api.voucher.router import router as voucher_router
from api.dashboard.router import router as dashboard_router
from api.indexer.router import router as indexer_router
from api.core.config import settings
from db.engine import get_db, init_db
from api.task.queries import create_multiple_tasks
from api.wallet.queries import create_initial_staking_options
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from admin import init_admin, SECRET_KEY
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI(
    title="Auth API",
    version="1.0.0"
)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

init_admin(app)


from fastapi.middleware.cors import CORSMiddleware


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With"],
    expose_headers=["Content-Length"],
    max_age=3600,
)


app.include_router(user_router)
app.include_router(wallet_router)
app.include_router(academy_router)
app.include_router(task_router)
app.include_router(voucher_router)
app.include_router(dashboard_router)
app.include_router(indexer_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=True
    )
