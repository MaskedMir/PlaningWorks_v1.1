from fastapi import HTTPException
from fastapi.params import Depends
import re

from sqlalchemy.dialects.postgresql import psycopg_async

from hash_passw import *

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import User  # Импорт модели User
from database import get_session  # Функция получения сессии


async def check_user_credentials(login: str, passw: str, session: AsyncSession = Depends(get_session)):
    # Проверяем совпадает ли пароль
    def verify_password(plain_password, hashed_password):
        hashed_password = str(hpassw(plain_password))
        if hashed_password == user.password:
            return True
        return False

    # Запрашиваем пользователя по имени
    result = await session.execute(select(User).where(User.username == login))
    user = result.scalars().first()

    if not user:
        print(f"Пользователь с логином {login} не найден.")
        return None

    if not verify_password(passw, user.password):
        print(f"Пароль для пользователя {login} неверный.")
        return None

    return True




async def register_user(login: str, email: str, password: str, session: AsyncSession):
    # Проверяем, существует ли пользователь с таким именем
    result = await session.execute(select(User).where(User.username == login))
    existing_user = result.scalars().first()

    result2 = await session.execute(select(User).where(User.email == email))
    existing_user_em = result2.scalars().first()

    # Если пользователь существует, выбрасываем исключение
    if existing_user:
        raise HTTPException(status_code=400, detail="Данное имя занято")

    # Хешируем пароль
    hashed_password = str(hpassw(password))
    if not is_valid_email(email):
        raise HTTPException(status_code=400, detail="Данный email некоректен")
    elif existing_user_em:
        raise HTTPException(status_code=400, detail="Данный email занят")

    # Создаем нового пользователя
    new_user = User(username=login, email=email, password=hashed_password)
    session.add(new_user)
    await session.commit()  # Сохраняем изменения в базе данных

    return {"message": "Вы зарегистрировались!"}



def is_valid_email(email: str) -> bool:
    """
    Проверяет, соответствует ли заданный email стандартному формату.
    Возвращает True, если email корректный, и False в противном случае.
    """
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None
