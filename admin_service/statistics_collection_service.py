from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models import User, Task
from database import get_session

import datetime
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


def collection_data():
    user_n = collection_user()
    task_n = collection_task()
    awr_task = int(task_n // user_n + 1)

    result = {"id": None,
              "user_n": user_n,
              "task_n": task_n,
              "awr_task": awr_task,
              "date": datetime.datetime.now().strftime("%Y-%m-%d")}\

    return result


async def collection_task(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Task))
    number = {"number_task": len(result.scalars().all())}

    return number


async def collection_user(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User))
    number = {"number_user": len(result.scalars().all())}

    return number

