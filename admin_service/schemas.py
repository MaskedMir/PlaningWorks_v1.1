from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class TaskRead(BaseModel):
    id: int
    name: str
    description: Optional[str]
    startime: Optional[datetime]
    finishtime: Optional[datetime]
    checked: bool
    user_id: int

    class Config:
        orm_mode = True

class UserRead(BaseModel):
    id: int
    username: str
    email: EmailStr

    class Config:
        orm_mode = True