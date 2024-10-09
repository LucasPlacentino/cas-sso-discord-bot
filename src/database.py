# -*- coding: utf-8 -*-
import logging
from os import getenv

#! OR USE SQLMODEL : https://sqlmodel.tiangolo.com/
#! OR ENCODE/DATABASES : https://www.encode.io/databases/
#from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .models import User

# TODO: use an ORM like SQLModel, SQLAlchemy, ormar or tortoise-orm, works with SQLite, PostgreSQL, and MySQL, and is async
#import sqlmodel # SQLModel is a wrapper around SQLAlchemy for combined use with Pydantic models so easier with FastAPI
#import ormar

# TODO: use Alembic for migrations (for SQLAlchemy)
#import alembic


DATABASE_URL = getenv("DATABASE_URL")
db_type = getenv("DB_TYPE")

# TODO: use UUIDs (v4) for primary keys ? (or Discord IDs ?) or the default incrementing integers ?

engine = create_async_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if db_type == "sqlite" else {},
    echo=True if getenv("DEBUG") else False
    )
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
    )
Base = declarative_base()

class database():
    #TODO: db actions for any db type
    if db_type == "gsheets": # see https://www.cdata.com/kb/tech/gsheets-python-sqlalchemy.rst
        from .gsheets_connector import GSheetsConnector # TODO:
        pass
    elif db_type == "mysql":
        pass
    elif db_type == "postgresql":
        pass
    elif db_type == "sqlite":
        pass
    else:
        raise NotImplementedError("DB_TYPE not implemented, must be one of \"gsheets\", \"mysql\", \"postgresql\", or \"sqlite\". Change this in your .env file.")

    def __init__(self):
        pass
    
    async def add_user(user: User):
        try:
            async with AsyncSession(engine) as session:
                pass
                #await session.commit()
        except Exception as e:
            raise self.DatabaseError(f"An error occurred while adding the user {user}: {e}")

    async def get_user(discord_user_id: int | None = None, cas_username: str | None = None) -> User:
        try:
            async with AsyncSession(engine) as session:
                pass
                #await session.commit()
        except Exception as e:
            raise self.DatabaseError(f"An error occurred while getting the user {discord_user_id} {cas_username}: {e}")

    async def delete_user(discord_user_id: int | None = None, cas_username: str | None = None):
        try:
            async with AsyncSession(engine) as session:
                pass
                #await session.commit()
        except Exception as e:
            raise self.DatabaseError(f"An error occurred while deleting the user {discord_user_id} {cas_username}: {e}")

    async def update_user(user: User):
        try:
            async with AsyncSession(engine) as session:
                pass
                #await session.commit()
        except Exception as e:
            raise self.DatabaseError(f"An error occurred while updating the user {user}: {e}")
    
    async def get_guild(discord_guild_id: int) -> Guild:
        try:
            async with AsyncSession(engine) as session:
                pass
                #await session.commit()
        except Exception as e:
            raise self.DatabaseError(f"An error occurred while getting the guild {discord_guild_id}: {e}")
    
    async def add_guild(guild: Guild):
        try:
            async with AsyncSession(engine) as session:
                pass
                #await session.commit()
        except Exception as e:
            raise self.DatabaseError(f"An error occurred while adding the guild {guild}: {e}")
    
    async def delete_guild(discord_guild_id: int):
        try:
            async with AsyncSession(engine) as session:
                pass
                #await session.commit()
        except Exception as e:
            raise self.DatabaseError(f"An error occurred while deleting the guild {discord_guild_id}: {e}")

    async def get_all_guilds() -> list[Guild]:
        try:
            async with AsyncSession(engine) as session:
                pass
                #await session.commit()
        except Exception as e:
            raise self.DatabaseError(f"An error occurred while getting all guilds: {e}")

    class DatabaseError(Exception):
        pass
