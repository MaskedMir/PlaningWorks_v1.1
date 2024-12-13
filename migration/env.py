
from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
import asyncio

from user_service.models import Base, User, Task, ServerStatus  # Добавьте все модели

target_metadata = Base.metadata
# Асинхронный движок
engine = create_async_engine("postgresql+asyncpg://adminka:huivamanedb@localhost:5432/planingworksdb", echo=True)

# Функция для синхронного выполнения асинхронных миграций
def run_sync(func):
    """Обертка для выполнения асинхронных операций синхронно"""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(func())

# Функция для миграции в онлайн-режиме
def run_migrations_online() -> None:
    """Основной процесс миграции в онлайн-режиме"""
    connectable = engine

    async def do_migrations():
        async with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                compare_type=True,
                compare_server_default=True,
            )

            with context.begin_transaction():
                context.run_migrations()

    run_sync(do_migrations)
