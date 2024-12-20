from datetime import timedelta
from fastapi import FastAPI, Depends, HTTPException, status, Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import User, Base
from database import engine, get_session
import os
import aio_pika
import asyncio
import logging
from authmodul import create_access_token, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES, oauth2_scheme
from schemas import UserCreate, UserRead, Token, LoginRequest
from loginreg import check_user_credentials, register_user
from blacklisted_tokens import blacklist_token
from fastapi.security import OAuth2PasswordRequestForm
from hash_passw import hpassw

app = FastAPI()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Конфигурация RabbitMQ
rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")


@app.on_event("startup")
async def startup():
    # Создание всех таблиц в базе данных
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Подключение к RabbitMQ с несколькими попытками
    max_attempts = 5
    for attempt in range(1, max_attempts + 1):
        try:
            connection = await aio_pika.connect_robust(rabbitmq_url)
            channel = await connection.channel()
            await channel.declare_queue("task_queue", durable=True)
            await channel.declare_queue("admin_queue", durable=True)
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


# Маршрут регистрации пользователя
@app.post("/register/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, session: AsyncSession = Depends(get_session)):
    new_user = await register_user(user.username, user.email, user.password, session)

    # Отправляем сообщение в очередь RabbitMQ асинхронно
    if app.state.rabbitmq_channel:
        try:
            message = aio_pika.Message(
                body=f"User {new_user.id} registered".encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )
            await app.state.rabbitmq_channel.default_exchange.publish(
                message,
                routing_key="task_queue",
            )
            logger.info(f"Сообщение о регистрации пользователя {new_user.id} отправлено в очередь")
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения в RabbitMQ: {e}")
            # Можно решить, как реагировать на ошибку, например, откатить транзакцию или уведомить администратора

    return new_user


# Маршрут авторизации (получение токена)
@app.post("/token/", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_session)):
    user = await check_user_credentials(form_data.username, form_data.password, session)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )

    if app.state.rabbitmq_channel:
        try:
            message = aio_pika.Message(
                body=f"{user.id}".encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )
            await app.state.rabbitmq_channel.default_exchange.publish(
                message,
                routing_key="task_queue",
            )
            logger.info(f"Сообщение о входе пользователя {user.id} отправлено в очередь")
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения в RabbitMQ: {e}")

    return {"access_token": access_token, "token_type": "bearer"}


# Маршрут выхода из аккаунта
@app.post("/logout/", response_model=dict)
async def logout(token: str = Depends(oauth2_scheme),
                 current_user: User = Depends(get_current_user),
                 session: AsyncSession = Depends(get_session)):
    try:
        # Добавляем токен в чёрный список
        blacklist_token(token)

        # Отправляем сообщение в очередь RabbitMQ асинхронно о выходе пользователя
        if app.state.rabbitmq_channel:
            try:
                message = aio_pika.Message(
                    body=f"{current_user.id}".encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                )
                await app.state.rabbitmq_channel.default_exchange.publish(
                    message,
                    routing_key="task_queue",
                )
                logger.info(f"Сообщение о выходе пользователя {current_user.id} отправлено в очередь")
            except Exception as e:
                logger.error(f"Ошибка при отправке сообщения в RabbitMQ: {e}")

        return {"message": "Вы успешно вышли из аккаунта"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при выходе: {str(e)}")


# Маршрут получения текущего пользователя (пример защищённого маршрута)
@app.get("/me/", response_model=UserRead)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


async def authenticate_admin(username: str, password: str, session: AsyncSession = Depends(get_session)):
    def verify_password(plain_password, hashed_password):
        if hpassw(plain_password) == hashed_password:
            return True
        return False

    # Получаем данные о пользователе
    result = await session.execute(select(User).where(User.username == username))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    #
    # if not verify_password(password, user.password):
    #     raise HTTPException(status_code=401, detail="Invalid password")

    # Проверяем, что это администратор
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")

    return user


# Эндпоинт для получения токена для админа
@app.post("/admin/login", response_model=Token)
async def admin_login(login_request: LoginRequest, session: AsyncSession = Depends(get_session)):
    user = await authenticate_admin(login_request.username, login_request.password, session)

    # Создаем JWT токен для администратора
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )

    if app.state.rabbitmq_channel:
        try:
            message = aio_pika.Message(
                body=f"{access_token}".encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )
            await app.state.rabbitmq_channel.default_exchange.publish(
                message,
                routing_key="admin_queue",
            )
            logger.info(f"Сообщение о входе пользователя {user.id} отправлено в очередь")
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения в RabbitMQ: {e}")

    logger.info(f"Admin {user.username} successfully logged in.")
    return {"access_token": access_token, "token_type": "bearer"}
