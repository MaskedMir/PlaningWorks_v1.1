from fastapi import FastAPI, Depends, HTTPException
from fastapi.params import Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from statistics_collection_service import collection_data
from models import User, Task, ServerStatus
from database import get_session
from typing import List
from schemas import UserRead, TaskRead, TaskNumber, CollectionNumber

import os
import aio_pika
import asyncio
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI()
rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")


@app.on_event("startup")
async def startup():
    max_attempts = 5
    for attempt in range(1, max_attempts + 1):
        try:
            connection = await aio_pika.connect_robust(rabbitmq_url)
            channel = await connection.channel()
            await channel.declare_queue("admin_queue", durable=True)
            app.rabbitmq_connection = connection
            app.rabbitmq_channel = channel
            logger.info("Успешное подключение к RabbitMQ")
            break
        except aio_pika.exceptions.AMQPConnectionError as e:
            logger.warning(f"Попытка подключения {attempt} не удалась: {e}")
            if attempt < max_attempts:
                await asyncio.sleep(5)
            else:
                logger.error("Не удалось подключиться к RabbitMQ после 5 попыток")
                app.rabbitmq_connection = None
                app.rabbitmq_channel = None


async def chek_admin_active():
    if not (hasattr(app, 'rabbitmq_channel') and app.rabbitmq_channel):
        logger.error("Не установлен канал RabbitMQ для потребления сообщений")

    logger.error("установлен канал RabbitMQ для потребления сообщений")
    queue = await app.rabbitmq_channel.declare_queue("admin_queue", durable=True)

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process():
                body = message.body.decode()
                logger.info(f"Получено сообщение: {body}")
                user_token = body
                return user_token


@app.on_event("shutdown")
async def shutdown():
    if hasattr(app, 'rabbitmq_connection') and app.rabbitmq_connection:
        await app.rabbitmq_connection.close()
        logger.info("Соединение с RabbitMQ закрыто")


@app.get("/admin/users/", response_model=List[UserRead])
async def get_users_by_ids(
        user_ids: List[int] = Query(..., alias="id", description="Список ID пользователей для получения данных"),
        session: AsyncSession = Depends(get_session)):
    chek = await chek_admin_active()
    if chek is None:
        raise HTTPException(status_code=444, detail="Пользователь не являеться администратором")
    else:
        result = await session.execute(select(User).where(User.id.in_(user_ids)))
        users = result.scalars().all()

        if not users:
            raise HTTPException(status_code=404, detail="Пользователи не найдены")

        return users


@app.get("/admin/tasks/", response_model=List[TaskRead])
async def get_tasks_by_ids(
        task_ids: List[int] = Query(..., alias="id", description="Список ID задач для получения данных"),
        session: AsyncSession = Depends(get_session)):
    chek = await chek_admin_active()
    if chek is None:
        raise HTTPException(status_code=444, detail="Пользователь не являеться администратором")
    else:
        result = await session.execute(select(Task).where(Task.id.in_(task_ids)))
        tasks = result.scalars().all()

        if not tasks:
            raise HTTPException(status_code=404, detail="Задачи не найдены")

        return tasks


@app.get("/admin/tasks/number/", response_model=TaskNumber)
async def get_tasks_by_ids(session: AsyncSession = Depends(get_session)):
    chek = await chek_admin_active()
    if chek is None:
        raise HTTPException(status_code=444, detail="Пользователь не являеться администратором")
    else:
        result = await session.execute(select(Task))

        number = {"number": len(result.scalars().all())}

        if not number:
            raise HTTPException(status_code=404, detail="Задачи не найдены")

        return number


@app.get("/admin/users/number/", response_model=TaskNumber)
async def get_user_by_ids(session: AsyncSession = Depends(get_session)):
    chek = await chek_admin_active()
    if chek is None:
        raise HTTPException(status_code=444, detail="Пользователь не являеться администратором")
    else:
        result = await session.execute(select(User))

        number = {"number": len(result.scalars().all())}

        if not number:
            raise HTTPException(status_code=404, detail="Пользователи не найдены")

        return number


@app.get("/admin/save/")
async def save_data(session: AsyncSession = Depends(get_session)):
    chek = await chek_admin_active()
    if chek is None:
        raise HTTPException(status_code=444, detail="Пользователь не является администратором")
    else:
        result = await collection_data(session)

        new_stat = ServerStatus(
            users_n=result.get("user_n"),
            task_n=result.get("task_n"),
            awr_task_n=result.get("awr_task_n"),
            date=result.get("date"),
        )
        session.add(new_stat)
        await session.commit()
        await session.refresh(new_stat)

        return {"message": "Статистика успешно сохранена"}
