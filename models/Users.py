from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Column, DateTime, Integer, String, ForeignKey, Float, Date, Boolean, TIMESTAMP
from typing import List, Optional

class Base(DeclarativeBase): pass

class Users(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    name: Mapped[str] = mapped_column(String(32), nullable=False)
    email: Mapped[str] = mapped_column(nullable=False, unique=True)
    password: Mapped[str] = mapped_column(nullable=False)

    stats: Mapped["UsersStats"] = relationship(back_populates="user")
    user_teams: Mapped[List["Users_Teams"]] = relationship(back_populates="user")
class UsersStats(Base):
    __tablename__ = "usersstats"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    tasks_amnt: Mapped[int]
    tasks_amnt_f: Mapped[int]
    tasks_amnt_nf: Mapped[int]
    tasks_amnt_st1: Mapped[int]
    tasks_amnt_st2: Mapped[int]
    tasks_amnt_st3: Mapped[int]
    tasks_amnt_st4: Mapped[int]
    avg_tasks_st: Mapped[float]
    users_statscol: Mapped[str]
    users_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    user: Mapped["Users"] = relationship(back_populates="stats")

class Users_Teams(Base):
    __tablename__ = "users_teams"

    users_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    teams_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))

    user: Mapped["Users"] = relationship(back_populates="user_teams")
    team: Mapped["Teams"] = relationship(back_populates="user_teams")
    tasks: Mapped[List["Tasks"]] = relationship(back_populates="")

class Teams(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    users_amnt: Mapped[int] = mapped_column()
    name: Mapped[str] = mapped_column(String(32))

    user_teams: Mapped[List["Users_Teams"]] = relationship(back_populates="team")

class Tasks(Base):
    __tablename__ = "tasks"
#Если может быть null, то убрать OPTIONAL!!!
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    start_t: Mapped[Optional[DateTime]] 
    finish_t: Mapped[Optional[DateTime]]
    est_time: Mapped[Optional[Float]]
    finished_at: Mapped[Optional[Date]]
    check_eng: Mapped[Optional[Boolean]]

    status_id: Mapped[int] = mapped_column(ForeignKey("status.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users_teams.users_id"))
    team_id: Mapped[int] = mapped_column(ForeignKey("users_teams.teams_id"))

    status: Mapped["Status"] = relationship(back_populates="tasks")
    user_teams: Mapped["Tasks"] = relationship(back_populates="tasks")
    

class Status(Base):
    __tablename__ = "status"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    desc: Mapped[Optional[str]] = mapped_column(String(45))

    tasks: Mapped[List["Tasks"]] = relationship(back_populates="status")

class Server_stats(Base):
    __tablename__ = "server_stats"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    users_amnt: Mapped[int]
    task_amnt: Mapped[int]
    avg_taasks_on_user: Mapped[float]
    date: Mapped[TIMESTAMP]

