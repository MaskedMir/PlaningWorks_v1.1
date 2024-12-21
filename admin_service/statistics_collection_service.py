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


async def collection_data(session: AsyncSession = Depends(get_session)):
    user_n = await collection_user(session)
    task_n = await collection_task(session)
    awr_task = int(task_n // user_n)

    result = {"user_n": user_n,
              "task_n": task_n,
              "awr_task_n": awr_task,
              "date": datetime.datetime.now()}

    return result


async def collection_task(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Task))
    number = int(len(result.scalars().all()))

    return number


async def collection_user(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User))
    number = int(len(result.scalars().all()))

    return number

