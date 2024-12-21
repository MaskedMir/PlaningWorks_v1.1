from datetime import timedelta
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from models import User, Base
from database import engine, get_session
import os
import aio_pika
import asyncio
import logging
from authmodul import create_access_token, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES, oauth2_scheme
from schemas import UserCreate, UserRead, Token
from loginreg import check_user_credentials, register_user
from blacklisted_tokens import blacklist_token

app = FastAPI()


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    max_attempts = 5
    for attempt in range(1, max_attempts + 1):
        try:
            connection = await aio_pika.connect_robust(rabbitmq_url)
            channel = await connection.channel()
            await channel.declare_queue("task_queue", durable=True)
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


@app.on_event("shutdown")
async def shutdown():

    if hasattr(app, 'rabbitmq_connection') and app.rabbitmq_connection:
        await app.rabbitmq_connection.close()
        logger.info("Соединение с RabbitMQ закрыто")


@app.post("/register/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, session: AsyncSession = Depends(get_session)):
    new_user = await register_user(user.username, user.email, user.password, session)

    if app.rabbitmq_channel:
        try:
            message = aio_pika.Message(
                body=f"User {new_user.id} registered".encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )
            await app.rabbitmq_channel.default_exchange.publish(
                message,
                routing_key="task_queue",
            )
            logger.info(f"Сообщение о регистрации пользователя {new_user.id} отправлено в очередь")
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения в RabbitMQ: {e}")

    return new_user



@app.post("/login/", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_session)):
    user = await check_user_credentials(form_data.username, form_data.password, session)
    if not user:
        raise HTTPException(status_code=401, detail="Нет такого пользователя")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )

    if app.rabbitmq_channel:
        try:
            message = aio_pika.Message(
                body=f"{user.id}".encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )
            await app.rabbitmq_channel.default_exchange.publish(
                message,
                routing_key="task_queue",
            )
            logger.info(f"Сообщение о входе пользователя {user.id} отправлено в очередь")
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения в RabbitMQ: {e}")

    return {"access_token": access_token, "token_type": "bearer"}



@app.post("/logout/", response_model=dict)
async def logout(token: str = Depends(oauth2_scheme),
                 current_user: User = Depends(get_current_user)):
    try:
        blacklist_token(token)
        if app.rabbitmq_channel:
            try:
                message = aio_pika.Message(
                    body=f"{current_user.id}".encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                )
                await app.rabbitmq_channel.default_exchange.publish(
                    message,
                    routing_key="task_queue",
                )
                logger.info(f"Сообщение о выходе пользователя {current_user.id} отправлено в очередь")
            except Exception as e:
                logger.error(f"Ошибка при отправке сообщения в RabbitMQ: {e}")

        return {"message": "Вы успешно вышли из аккаунта"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при выходе: {str(e)}")



@app.get("/me/", response_model=UserRead)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@app.post("/admin/login", response_model=Token)
async def admin_login(username: str, password: str, session: AsyncSession = Depends(get_session)):
    user = await check_user_credentials(username, password, session)

    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )

    if app.rabbitmq_channel:
        try:
            message = aio_pika.Message(
                body=f"{access_token}".encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )
            await app.rabbitmq_channel.default_exchange.publish(
                message,
                routing_key="admin_queue",
            )
            logger.info(f"Сообщение о входе пользователя {user.id} отправлено в очередь")
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения в RabbitMQ: {e}")

    logger.info(f"Admin {user.username} successfully logged in.")
    return {"access_token": access_token, "token_type": "bearer"}
