from fastapi import FastAPI, Depends, HTTPException
from fastapi.params import Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import User, Task
from database import get_session
from typing import List
from schemas import UserRead, TaskRead
import os
import aio_pika
import asyncio
import logging


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI()

# Конфигурация RabbitMQ
rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")


@app.on_event("startup")
async def startup():
    # Подключение к RabbitMQ с несколькими попытками

    max_attempts = 5
    for attempt in range(1, max_attempts + 1):
        try:
            connection = await aio_pika.connect_robust(rabbitmq_url)
            channel = await connection.channel()
            await channel.declare_queue("task_queue", durable=True)
            app.state.rabbitmq_connection = connection
            app.state.rabbitmq_channel = channel
            logger.info("Успешное подключение к RabbitMQ")
            break
        except aio_pika.exceptions.AMQPConnectionError as e:
            logger.warning(f"Попытка подключения {attempt} не удалась: {e}")
            if attempt < max_attempts:
                await asyncio.sleep(5)
            else:
                logger.error("Не удалось подключиться к RabbitMQ после 5 попыток")
                app.state.rabbitmq_connection = None
                app.state.rabbitmq_channel = None


@app.on_event("shutdown")
async def shutdown():
    # Закрытие соединения с RabbitMQ
    if hasattr(app.state, 'rabbitmq_connection') and app.state.rabbitmq_connection:
        await app.state.rabbitmq_connection.close()
        logger.info("Соединение с RabbitMQ закрыто")




# Админский эндпоинт для получения данных пользователей по их ID
@app.get("/admin/users/", response_model=List[UserRead])
async def get_users_by_ids(
    user_ids: List[int] = Query(..., alias="id", description="Список ID пользователей для получения данных"),
    session: AsyncSession = Depends(get_session)
):
    # Запросим пользователей по ID
    result = await session.execute(select(User).where(User.id.in_(user_ids)))
    users = result.scalars().all()

    # Если не найдено ни одного пользователя, возвращаем ошибку
    if not users:
        raise HTTPException(status_code=404, detail="Пользователи не найдены")

    return users

# Админский эндпоинт для получения данных задач по их ID
@app.get("/admin/tasks/", response_model=List[TaskRead])
async def get_tasks_by_ids(
    task_ids: List[int] = Query(..., alias="id", description="Список ID задач для получения данных"),
    session: AsyncSession = Depends(get_session)
):
    # Запросим задачи по ID
    result = await session.execute(select(Task).where(Task.id.in_(task_ids)))
    tasks = result.scalars().all()

    # Если не найдено ни одной задачи, возвращаем ошибку
    if not tasks:
        raise HTTPException(status_code=404, detail="Задачи не найдены")

    return tasks