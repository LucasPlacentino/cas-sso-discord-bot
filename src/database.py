# -*- coding: utf-8 -*-
import logging
from os import getenv

from collections.abc import AsyncGenerator # The AsyncGenerator type hint is a special type hint that is used for asynchronous generators (type hint for the get_db function)

#! OR USE SQLMODEL : https://sqlmodel.tiangolo.com/
#from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .models import User, Guild

# TODO: use an ORM like SQLModel, SQLAlchemy, ormar or tortoise-orm, works with SQLite, PostgreSQL, and MySQL, and is async
#import sqlmodel # SQLModel is a wrapper around SQLAlchemy for combined use with Pydantic models so easier with FastAPI
#import ormar

# TODO: use Alembic for migrations (for SQLAlchemy)
#import alembic


DATABASE_URL = getenv("DATABASE_URL")
db_type = getenv("DB_TYPE")

# TODO: use UUIDs (v4) for primary keys ? (or Discord IDs ?) or the default incrementing integers ?

#engine = create_async_engine(
#    DATABASE_URL,
#    connect_args={"check_same_thread": False} if db_type == "sqlite" else {},
#    echo=True if getenv("DEBUG") else False
#    )
#SessionLocal = sessionmaker(
#    autocommit=False,
#    autoflush=False,
#    bind=engine
#    )
Base = declarative_base()

logger = logging.getLogger("db")
if getenv("DEBUG"):
    #logging.basicConfig(level=logging.DEBUG)
    logging.basicConfig(
        level=logging.DEBUG,
        format="{asctime} [{threadName}] ({filename}:{lineno}) [{levelname}]  {message}", # [{threadName}]
        style="{",
        datefmt="%Y-%m-%d %H:%M"
    )
    logger.info("Debug mode enabled")
else:
    logging.basicConfig(
        level=logging.INFO,
        format="{asctime} [{filename}:{lineno}-{levelname}]  {message}", # [{threadName}]
        style="{",
        datefmt="%Y-%m-%d %H:%M"
    )

class database():

    def __init__(self):
        self.__engine_connect_args = {}
        #TODO: db actions for any db type
        if db_type in ["gsheets", "googlesheets"]: # see https://www.cdata.com/kb/tech/gsheets-python-sqlalchemy.rst
            from .gsheets_connector import GSheetsConnector # TODO:
            #self.DATABASE_URL = "googlesheets://user:pass@spreadsheet_id"

            logger.info(f"DB: Connecting to Google Sheets database at {self.DATABASE_URL}")
            pass
        elif db_type == "mysql":
            self.DATABASE_URL = "mysql+aiomysql://root:root@localhost/test"
            self.DATABASE_URL = f"mysql+aiomysql://{getenv('DB_USER')}:{getenv('DB_PASSWORD')}@{getenv('DB_SERVER')}/{getenv('DB')}"
            logger.info(f"DB: Connecting to MySQL database at {self.DATABASE_URL}")
            pass
        elif db_type in ["postgresql", "postgres"]:
            self.DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost/postgres" #or getenv("DATABASE_URL")
            self.DATABASE_URL = f"postgresql+asyncpg://{getenv('DB_USER')}:{getenv('DB_PASSWORD')}@{getenv('DB_SERVER')}/{getenv('DB')}"
            logger.info(f"DB: Connecting to PostgreSQL database at {self.DATABASE_URL}")
            pass
        elif db_type == "sqlite":
            self.DATABASE_URL = "sqlite+aiosqlite:///./test.db" #or getenv("DATABASE_URL")
            logger.info(f"DB: Connecting to SQLite database at {self.DATABASE_URL}")
            self.__engine_connect_args = {"check_same_thread": False} # needed for SQLite
            pass
        else:
            raise NotImplementedError("DB_TYPE not implemented, must be one of \"gsheets\", \"mysql\", \"postgresql\", or \"sqlite\". Change this in your .env file.")
        pass

        self.async_engine = create_async_engine(
                self.DATABASE_URL,
                connect_args=self.__engine_connect_args,
                echo=True if getenv("DEBUG") else False
            )
        self.async_session = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.async_engine,
            expire_on_commit=False
        )
    
    async def __get_db() -> AsyncGenerator:
        """Get a database session.
        To be used for dependency injection.
        """
        async with self.async_session() as session, session.begin():
            yield session

    async def __init_db_models():
        """Create tables if they don't already exist.
        In a real-life example we would use TODO:Alembic to manage migrations.
        """
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def add_user(user: User):
        try:
            async with AsyncSession(self.async_engine) as session:
                pass
                #await session.commit()
        except Exception as e:
            raise DatabaseError(f"An error occurred while adding the user {user}: {e}")

    async def get_user(discord_user_id: int | None = None, cas_username: str | None = None) -> User:
        try:
            async with AsyncSession(self.async_engine) as session:
                pass
                #await session.commit()
        except Exception as e:
            raise DatabaseError(f"An error occurred while getting the user {discord_user_id} {cas_username}: {e}")

    async def delete_user(discord_user_id: int | None = None, cas_username: str | None = None):
        try:
            async with AsyncSession(self.async_engine) as session:
                pass
                #await session.commit()
        except Exception as e:
            raise DatabaseError(f"An error occurred while deleting the user {discord_user_id} {cas_username}: {e}")

    async def update_user(user: User):
        try:
            async with AsyncSession(self.async_engine) as session:
                pass
                #await session.commit()
        except Exception as e:
            raise DatabaseError(f"An error occurred while updating the user {user}: {e}")
        
    async def user_linked_discord(cas_username: str) -> bool:
        try:
            async with AsyncSession(self.async_engine) as session:
                pass
                #await session.commit()
        except Exception as e:
            raise DatabaseError(f"An error occurred while checking if the user {cas_username} is linked to Discord: {e}")
    
    async def get_guild(discord_guild_id: int) -> Guild:
        try:
            async with AsyncSession(self.async_engine) as session:
                pass
                #await session.commit()
        except Exception as e:
            raise DatabaseError(f"An error occurred while getting the guild {discord_guild_id}: {e}")
    
    async def add_guild(guild: Guild):
        try:
            async with AsyncSession(self.async_engine) as session:
                pass
                #await session.commit()
        except Exception as e:
            raise DatabaseError(f"An error occurred while adding the guild {guild}: {e}")
    
    async def delete_guild(discord_guild_id: int):
        try:
            async with AsyncSession(self.async_engine) as session:
                pass
                #await session.commit()
        except Exception as e:
            raise DatabaseError(f"An error occurred while deleting the guild {discord_guild_id}: {e}")

    async def get_all_guilds() -> list[Guild]:
        try:
            async with AsyncSession(self.async_engine) as session:
                pass
                #await session.commit()
        except Exception as e:
            raise DatabaseError(f"An error occurred while getting all guilds: {e}")

class DatabaseError(Exception):
    def __init__(self, message: str):
        self.message = message
        logging.error("DB: "+message)
        super().__init__(message)
    
    def __str__(self):
        return self.message

