# QuantexApi

API сервер для проекта Quantex, разработанный на Python с использованием FastAPI.

## Описание

Этот проект представляет собой серверную часть приложения Quantex, обеспечивающую следующий функционал:
- Аутентификация и авторизация пользователей
- Управление академией
- Управление задачами
- Работа с кошельками
- Панель управления
- Система ваучеров
- Интеграция с различными блокчейнами (ETH, BSC, TON)

## Технологический стек

- Python 3.8+
- FastAPI
- SQLAlchemy
- Alembic (для миграций)
- PostgreSQL
- JWT для аутентификации
- Pydantic для валидации данных

## Установка и запуск

### Локальный запуск

1. Клонируйте репозиторий:
```bash
git clone git@github.com:AndyNortonDev/QuantexApi.git
cd QuantexApi
```

2. Создайте виртуальное окружение и активируйте его:
```bash
python -m venv venv
source venv/bin/activate  # для Linux/Mac
# или
venv\Scripts\activate  # для Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Создайте файл .env и настройте переменные окружения:
```
# База данных
DATABASE_URL=postgresql://user:password@localhost:5432/db_name

# JWT
JWT_SECRET_KEY=your_secret_key

# Индексеры
ETH_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/your-api-key
BSC_RPC_URL=https://bsc-dataseed.binance.org
TON_API_KEY=your_ton_api_key
```

5. Примените миграции:
```bash
alembic upgrade head
```

6. Запустите сервер:
```bash
python src/main.py
```

### Запуск через Docker

1. Клонируйте репозиторий:
```bash
git clone git@github.com:AndyNortonDev/QuantexApi.git
cd QuantexApi
```

2. Создайте файл .env с необходимыми переменными окружения (как описано выше)

3. Запустите приложение с помощью Docker Compose:
```bash
docker-compose up -d
```

Приложение будет доступно по адресу http://localhost:8000

Для остановки приложения:
```bash
docker-compose down
```

## Работа с Pydantic

В проекте используется Pydantic для валидации данных и сериализации/десериализации. Основные модели находятся в файлах `schemas.py` каждого модуля.

Пример использования:

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., regex=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    password: str = Field(..., min_length=8)
    
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
```

## Структура проекта

```
.
├── alembic.ini                 # Конфигурация Alembic для миграций
├── requirements.txt            # Зависимости проекта
├── README.md                   # Документация проекта
├── Dockerfile                  # Конфигурация Docker
├── docker-compose.yml         # Конфигурация Docker Compose
└── src/                       # Исходный код
    ├── admin/                 # Административная панель
    │   ├── admin_panel.py     # Реализация админ-панели
    │   └── schemas.py         # Схемы данных для админ-панели
    │
    ├── api/                   # API endpoints
    │   ├── academy/          # Модуль академии
    │   │   ├── queries.py    # SQL запросы
    │   │   ├── router.py     # FastAPI роутер
    │   │   ├── service.py    # Бизнес-логика
    │   │   └── shemas.py     # Pydantic модели
    │   │
    │   ├── auth/            # Аутентификация
    │   │   ├── certs/       # JWT сертификаты
    │   │   ├── crt_tokens.py # Создание токенов
    │   │   ├── utils.py     # Вспомогательные функции
    │   │   └── validation.py # Валидация токенов
    │   │
    │   ├── core/            # Ядро приложения
    │   │   ├── config.py    # Конфигурация
    │   │   ├── error.py     # Обработка ошибок
    │   │   ├── logger/      # Система логирования
    │   │   └── save_image.py # Работа с изображениями
    │   │
    │   ├── dashboard/       # Панель управления
    │   │   ├── queries.py   # SQL запросы
    │   │   ├── router.py    # FastAPI роутер
    │   │   ├── service.py   # Бизнес-логика
    │   │   └── shemas.py    # Pydantic модели
    │   │
    │   ├── task/           # Управление задачами
    │   │   ├── queries.py  # SQL запросы
    │   │   ├── router.py   # FastAPI роутер
    │   │   ├── service.py  # Бизнес-логика
    │   │   └── shemas.py   # Pydantic модели
    │   │
    │   ├── user/           # Управление пользователями
    │   │   ├── crud.py     # CRUD операции
    │   │   ├── route.py    # FastAPI роутер
    │   │   ├── service.py  # Бизнес-логика
    │   │   └── shemas.py   # Pydantic модели
    │   │
    │   ├── voucher/        # Система ваучеров
    │   │   ├── queries.py  # SQL запросы
    │   │   ├── router.py   # FastAPI роутер
    │   │   ├── service.py  # Бизнес-логика
    │   │   └── shemas.py   # Pydantic модели
    │   │
    │   └── wallet/         # Управление кошельками
    │       ├── queries.py  # SQL запросы
    │       ├── router.py   # FastAPI роутер
    │       ├── service.py  # Бизнес-логика
    │       └── schemas.py  # Pydantic модели
    │
    ├── bot/                # Telegram бот
    │   └── bot.py         # Реализация бота
    │
    ├── db/                 # Работа с базой данных
    │   ├── engine.py      # Подключение к БД
    │   ├── models.py      # SQLAlchemy модели
    │   ├── queries.sql    # Сырые SQL запросы
    │   └── migrations/    # Миграции Alembic
    │       └── versions/  # Версии миграций
    │
    └── main.py           # Точка входа приложения
```

## Лицензия

MIT