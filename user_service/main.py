from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from models import User, Base
from database import engine, get_session
from sqlalchemy import select
import os
import pika
import time

from loginreg import check_user_credentials, register_user

rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
params = pika.URLParameters(rabbitmq_url)

# Пробуем подключиться к RabbitMQ с несколькими попытками
for attempt in range(5):
    try:
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        channel.queue_declare(queue="user_queue")
        print("Успешное подключение к RabbitMQ")
        break
    except pika.exceptions.AMQPConnectionError as e:
        print(f"Попытка подключения {attempt + 1} не удалась, повтор через 5 секунд...")
        time.sleep(5)
else:
    print("Не удалось подключиться к RabbitMQ после 5 попыток")

app = FastAPI()


# Создание таблиц
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Подключение к RabbitMQ
import os
import pika

rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
params = pika.URLParameters(rabbitmq_url)
connection = pika.BlockingConnection(params)
channel = connection.channel()
channel.queue_declare(queue="user_queue")


# Асинхронное добавление пользователя
@app.post("/users/")
async def create_user(name: str, email: str, password: str, session: AsyncSession = Depends(get_session)):
    new_user = User(username=name, email=email, password=password)
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    # Отправляем сообщение в очередь RabbitMQ
    channel.basic_publish(exchange='', routing_key="user_queue", body=f"User {new_user.id} created")

    return new_user


# Получение списка пользователей

@app.get("/users/")
async def get_users(session: AsyncSession = Depends(get_session)):
    # Используем select для запроса всех пользователей

    result = await session.execute(select(User))
    users = result.scalars().all()  # Получаем все результаты как объекты User
    return users


@app.post("/login/")
async def login(login: str, password: str, session: AsyncSession = Depends(get_session)):
    is_authenticated = await check_user_credentials(login, password, session)

    if not is_authenticated:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {"message": "Авторизация успешная"}

@app.post("/register/")
async def register(login: str, email: str, password: str, session: AsyncSession = Depends(get_session)):
    return await register_user(login, email, password, session)