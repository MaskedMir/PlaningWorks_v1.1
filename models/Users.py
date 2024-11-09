from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Column, DateTime, Integer, String, ForeignKey, Float, Date, Boolean
from typing import List, Optional

class Base(DeclarativeBase): pass

class Users(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    name: Mapped[str] = mapped_column(String(32), nullable=False)
    email: Mapped[str] = mapped_column(nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)

    tasks: Mapped[List["Tasks"]] = relationship(back_populates="user")
    stats: Mapped["UsersStats"] = relationship(back_populates="user")
class UsersStats(Base):
    __tablename__ = "usersstats"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    tasks_amnt: Mapped[int] = mapped_column(nullable=False)
    tasks_amnt_f: Mapped[int] = mapped_column(nullable=False)
    tasks_amnt_nf: Mapped[int] = mapped_column(nullable=False)
    tasks_amnt_st1: Mapped[int] = mapped_column(nullable=False)
    tasks_amnt_st2: Mapped[int] = mapped_column(nullable=False)
    tasks_amnt_st3: Mapped[int] = mapped_column(nullable=False)
    tasks_amnt_st4: Mapped[int] = mapped_column(nullable=False)
    avg_tasks_st: Mapped[float] = mapped_column(nullable=False)
    users_statscol: Mapped[str] = mapped_column(nullable=False)
    users_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    user: Mapped["Users"] = relationship(back_populates="stats")

class Teams(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    users_amnt: Mapped[int] = mapped_column()
    name: Mapped[str] = mapped_column(String(32))

    users: Mapped[List["Users"]] = relationship(secondary=users_teams, back_populates="teams")
    tasks: Mapped[List["Tasks"]] = relationship(back_populates="team")

class Tasks(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    start_t: Mapped[Optional[DateTime]]
    finish_t: Mapped[Optional[DateTime]]
    est_time: Mapped[Optional[Float]]
    finished_at: Mapped[Optional[Date]]
    check_eng: Mapped[Optional[Boolean]]

    status_id: Mapped[int] = mapped_column(ForeignKey("status.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))

    status: Mapped["Status"] = relationship(back_populates="tasks")
    user: Mapped["Users"] = relationship(back_populates="tasks")
    team: Mapped["Teams"] = relationship(back_populates="tasks")

class Status(Base):
    __tablename__ = "status"

    id: Mapped[int] = mapped_column(primary_key=True)
    disc: Mapped[str] = mapped_column(String(45))

    tasks: Mapped[List["Tasks"]] = relationship(back_populates="status")

