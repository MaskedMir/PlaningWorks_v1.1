from fastapi import FastAPI, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from models import Task
from database import get_session
from typing import Optional
from datetime import datetime
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
            await channel.declare_queue("task_queue", durable=True)
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


@app.on_event("shutdown")
async def shutdown():
    # Закрытие соединения с RabbitMQ
    if hasattr(app, 'rabbitmq_connection') and app.rabbitmq_connection:
        await app.rabbitmq_connection.close()
        logger.info("Соединение с RabbitMQ закрыто")



class TaskCreate(BaseModel):
    name: str
    description: str
    startime: datetime
    finishtime: datetime
    checked: bool



@app.get("/get_user_tasks/")
async def get_user_tasks(session: AsyncSession = Depends(get_session)):
    if not (hasattr(app, 'rabbitmq_channel') and app.rabbitmq_channel):
        logger.error("Не установлен канал RabbitMQ для потребления сообщений")

    queue = await app.rabbitmq_channel.declare_queue("task_queue", durable=True)

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process():
                body = message.body.decode()
                logger.info(f"Получено сообщение: {body}")
                user_id = int(body)
                try:
                    result = await session.execute(select(Task).where(Task.user_id == user_id))
                    tasks = result.scalars().all()
                    return tasks
                except Exception as e:
                    logger.error(f"Ошибка при получении задач: {e}")
                    raise HTTPException(status_code=500, detail=f"Ошибка при получении задач: {str(e)}")


@app.post("/post_user_task/")
async def post_user_task(task: TaskCreate, session: AsyncSession = Depends(get_session)):
    if not (hasattr(app, 'rabbitmq_channel') and app.rabbitmq_channel):
        logger.error("Не установлен канал RabbitMQ для потребления сообщений")

    queue = await app.rabbitmq_channel.declare_queue("task_queue", durable=True)

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process():
                body = message.body.decode()
                logger.info(f"Получено сообщение: {body}")
                user_id = int(body)

                try:
                    new_task = Task(
                        name=task.name,
                        description=task.description,
                        startime=task.startime,
                        finishtime=task.finishtime,
                        checked=task.checked,
                        user_id=user_id
                    )

                    session.add(new_task)
                    await session.commit()
                    await session.refresh(new_task)

                    if hasattr(app, 'rabbitmq_channel') and app.rabbitmq_channel:
                        try:
                            message_body = f"Task {new_task.id} created for User {new_task.user_id}".encode()
                            message = aio_pika.Message(
                                body=message_body,
                                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                            )
                            await app.rabbitmq_channel.default_exchange.publish(
                                message,
                                routing_key="task_queue",
                            )
                            logger.info(f"Сообщение о создании задачи {new_task.id} отправлено в очередь")
                        except aio_pika.exceptions.AMQPError as e:
                            logger.error(f"Ошибка при отправке сообщения: {e}")

                    return {"message": "Задача успешно создана", "task_id": new_task.id}

                except Exception as e:
                    await session.rollback()
                    logger.error(f"Ошибка при создании задачи: {e}")
                    raise HTTPException(status_code=500, detail=f"Ошибка при создании задачи: {str(e)}")


@app.patch("/update_user_task/{task_id}/")
async def update_user_task(
        task_id: int = Path(),
        name: Optional[str] = None,
        description: Optional[str] = None,
        startime: Optional[datetime] = None,
        finishtime: Optional[datetime] = None,
        checked: Optional[bool] = None,
        user_id: Optional[int] = None,
        session: AsyncSession = Depends(get_session)
):
    try:
        result = await session.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(status_code=404, detail="Задача не найдена")

        if name is not None:
            task.name = name
        if description is not None:
            task.description = description
        if startime is not None:
            task.startime = startime
        if finishtime is not None:
            task.finishtime = finishtime
        if checked is not None:
            task.checked = checked
        if user_id is not None:
            task.user_id = user_id

        session.add(task)
        await session.commit()
        await session.refresh(task)

        return {"message": "Задача успешно обновлена", "task_id": task.id}

    except HTTPException as he:
        raise he
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при обновлении задачи: {str(e)}")


@app.delete("/delete_user_task/{task_id}/")
async def delete_user_task(
        task_id: int = Path(),
        session: AsyncSession = Depends(get_session)):
    try:
        # Поиск задачи по ID
        result = await session.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(status_code=404, detail="Задача не найдена")

        await session.delete(task)
        await session.commit()

        return {"message": "Задача успешно удалена", "task_id": task_id}

    except HTTPException as he:
        raise he
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении задачи: {str(e)}")
