import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Column, DateTime, Integer, String, ForeignKey, Float, Date, Boolean
from typing import List, Optional

from db_handler.database import Base

class Users(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False)
    name: Mapped[str] = mapped_column(String(32), nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String, nullable=False)

    stats: Mapped["UsersStats"] = relationship(back_populates="user")


class UsersStats(Base):
    __tablename__ = "usersstats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False)
    tasks_amnt: Mapped[int] = mapped_column(Integer, nullable=False)
    tasks_amnt_f: Mapped[int] = mapped_column(Integer, nullable=False)
    tasks_amnt_nf: Mapped[int] = mapped_column(Integer, nullable=False)
    tasks_amnt_st1: Mapped[int] = mapped_column(Integer, nullable=False)
    tasks_amnt_st2: Mapped[int] = mapped_column(Integer, nullable=False)
    tasks_amnt_st3: Mapped[int] = mapped_column(Integer, nullable=False)
    tasks_amnt_st4: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_tasks_st: Mapped[float] = mapped_column(Float, nullable=False)
    users_statscol: Mapped[str] = mapped_column(String, nullable=False)
    users_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    user: Mapped["Users"] = relationship(back_populates="stats")


class Tasks(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False)
    start_t: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    finish_t: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    est_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    finished_at: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    check_eng: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    status_id: Mapped[int] = mapped_column(ForeignKey("status.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))

    status: Mapped["Status"] = relationship(back_populates="tasks")
    user: Mapped["Users"] = relationship("Users")
    team: Mapped["Teams"] = relationship("Teams")


class Status(Base):
    __tablename__ = "status"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False)
    desc: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)

    tasks: Mapped[List["Tasks"]] = relationship(back_populates="status")


class ServerStats(Base):
    __tablename__ = "server_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False)
    users_amnt: Mapped[int] = mapped_column(Integer, nullable=False)
    task_amnt: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_tasks_on_user: Mapped[float] = mapped_column(Float, nullable=False)
    date: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
