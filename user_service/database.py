from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    raise ValueError("DATABASE_URL не установлен. Проверьте настройки в docker-compose.yml")

# Создаем асинхронный движок
engine = create_async_engine(DATABASE_URL, echo=True)

# Создаем асинхронную сессию
async_session = async_sessionmaker(
    bind=engine, expire_on_commit=False
)


# Функция для получения сессии
async def get_session():
    async with async_session() as session:
        yield session
