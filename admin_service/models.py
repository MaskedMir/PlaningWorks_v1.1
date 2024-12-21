from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean

# Используем асинхронный движок
engine = create_async_engine('postgresql+asyncpg://adminka:huivamanedb@localhost:5432/planingworksdb', echo=True)

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    role = Column(String(255), nullable=False)


class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text, nullable=False)
    startime = Column(DateTime, nullable=False)
    finishtime = Column(DateTime, nullable=False)
    checked = Column(Boolean, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)


class ServerStatus(Base):
    __tablename__ = "server_status"
    id = Column(Integer, primary_key=True)
    users_n = Column(Integer, nullable=False)
    task_n = Column(Integer, nullable=False)
    awr_task_n = Column(Integer, nullable=False)
    date = Column(DateTime, nullable=False)
