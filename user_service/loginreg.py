from fastapi import HTTPException, status
import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import User
from hash_passw import hpassw


def is_valid_email(email: str) -> bool:
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None


async def check_user_credentials(login: str, passw: str, session: AsyncSession):
    # Запрашиваем пользователя по имени
    result = await session.execute(select(User).where(User.username == login))
    user = result.scalars().first()

    if not user:
        print(f"Пользователь с логином {login} не найден.")
        return None

    # Проверяем совпадает ли пароль
    hashed_password = str(hpassw(passw))
    if hashed_password != user.password:
        print(f"Пароль для пользователя {login} неверный.")
        return None

    return user  # Возвращаем объект пользователя для дальнейшего использования



async def register_user(login: str, email: str, password: str, session: AsyncSession):
    # Проверяем, существует ли пользователь с таким именем
    result = await session.execute(select(User).where(User.username == login))
    existing_user = result.scalars().first()

    result2 = await session.execute(select(User).where(User.email == email))
    existing_user_em = result2.scalars().first()

    # Если пользователь существует, выбрасываем исключение
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Данное имя занято")

    # Хешируем пароль
    hashed_password = str(hpassw(password))
    if not is_valid_email(email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Данный email некорректен")
    elif existing_user_em:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Данный email занят")

    # Создаем нового пользователя
    new_user = User(username=login, email=email, password=hashed_password)
    session.add(new_user)
    try:
        await session.commit()  # Сохраняем изменения в базе данных
        await session.refresh(new_user)
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Регистрация не удалась")

    return new_user
