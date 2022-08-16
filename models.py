from enum import Enum as MAIN_ENUM
from typing import List

from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Enum, Integer, String, Text
from sqlalchemy.sql import func

from database import Base
from pydantic_sqlalchemy.pydantic_sqlalchemy import sqlalchemy_to_pydantic


class Status(str, MAIN_ENUM):
    draft = "Draft"
    publish = "Publish"
    archive = "Archive"


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, unique=True)
    content = Column(Text)
    status = Column(Enum(Status))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


PydanticPost = sqlalchemy_to_pydantic(Post)


class ListPydanticPost(BaseModel):
    posts: List[PydanticPost]
