# -*- coding: utf-8 -*-
import logging
from os import getenv

from collections.abc import AsyncGenerator # The AsyncGenerator type hint is a special type hint that is used for asynchronous generators (type hint for the get_db function)

#* OR USE SQLMODEL : https://sqlmodel.tiangolo.com/
#from sqlalchemy import create_engine
#from sqlalchemy.ext.asyncio import create_async_engine
#from sqlalchemy.ext.asyncio.session import AsyncSession
#from sqlalchemy.ext.declarative import declarative_base
#from sqlalchemy.orm import sessionmaker

from .models import User, Guild

# TODO: use an ORM like SQLModel, SQLAlchemy, ormar or tortoise-orm, works with SQLite, PostgreSQL, and MySQL, and is async
#import sqlmodel # SQLModel is a wrapper around SQLAlchemy for combined use with Pydantic models so easier with FastAPI
import ormar # based on SQLAlchemy Core so works with Alembic
#from ormar import Extra
import sqlalchemy
import databases

# TODO: use Alembic for migrations (for SQLAlchemy)
#import alembic


DATABASE_URL = getenv("DATABASE_URL")
db_type = getenv("DB_TYPE")
__database = databases.Database(DATABASE_URL)
__metadata = sqlalchemy.MetaData()

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
#Base = declarative_base()

base_ormar_config = ormar.ModelMeta( # ormar.OrmarConfig() #?
    database=__database, # or __database or DATABASE_URL
    metadata=__metadata, # =Base.metadata, # =sqlalchemy.MetaData()
    engine=sqlalchemy.create_engine(DATABASE_URL),
    #abstract=True,
    #extra=Extra.ignore  # set extra setting to prevent exceptions on extra fields presence
)

logger = logging.getLogger("db")

#if getenv("DEBUG"):
#    #logging.basicConfig(level=logging.DEBUG)
#    logging.basicConfig(
#        level=logging.DEBUG,
#        format="{asctime} [{threadName}] ({filename}:{lineno}) [{levelname}]  {message}", # [{threadName}]
#        style="{",
#        datefmt="%Y-%m-%d %H:%M"
#    )
#    logger.info("Debug mode enabled")
#else:
#    logging.basicConfig(
#        level=logging.INFO,
#        format="{asctime} [{filename}:{lineno}-{levelname}]  {message}", # [{threadName}]
#        style="{",
#        datefmt="%Y-%m-%d %H:%M"
#    )

class DB():
    async def add_user(user: User):
        try:
            logger.debug(f"Adding user {user} to the database")
            await user.save()
        except Exception as e:
            raise DatabaseError(f"An error occurred while adding the user {user}: {e}")
        
    async def delete_user(discord_user_id: int | None = None, cas_username: str | None = None):
        try:
            logger.debug(f"Deleting user {discord_user_id} {cas_username} from the database")
            if discord_user_id:
                await User.objects.delete(discord_id=discord_user_id)
            elif cas_username:
                await User.objects.delete(cas_username=cas_username)
            else:
                raise ValueError("Either discord_user_id or cas_username must be provided")
        except Exception as e:
            raise DatabaseError(f"An error occurred while deleting the user {discord_user_id} {cas_username}: {e}")

    async def user_linked_discord(cas_username: str) -> bool:
        try:
            logger.debug(f"Checking if the user {cas_username} is linked to Discord (checking if user exists in the database)")
            # A user exists in the database IF AND ONLY IF they have linked their Discord account to their CAS account (reduces size of database and eases user deletion)
            return await User.objects.filter(cas_username=cas_username).exists()
        except Exception as e:
            raise DatabaseError(f"An error occurred while checking if the user {cas_username} is linked to Discord: {e}")
    
    async def get_guild(discord_guild_id: int) -> Guild:
        try:
            logger.debug(f"Getting the guild {discord_guild_id} from the database")
            guild = await Guild.objects.get(discord_guild_id=discord_guild_id)
            return guild
        except Exception as e:
            raise DatabaseError(f"An error occurred while getting the guild {discord_guild_id}: {e}")
        
    async def add_guild(guild: Guild):
        try:
            logger.debug(f"Adding guild {guild} to the database")
            await guild.save()
        except Exception as e:
            raise DatabaseError(f"An error occurred while adding the guild {guild}: {e}")
    
    async def delete_guild(discord_guild_id: int):
        try:
            logger.debug(f"Deleting guild {discord_guild_id} from the database")
            await Guild.objects.delete(discord_guild_id=discord_guild_id) # delete using a query
            #? or
            #await Guild.objects.get(discord_guild_id=discord_guild_id).delete() # delete using a Model instance
        except Exception as e:
            raise DatabaseError(f"An error occurred while deleting the guild {discord_guild_id}: {e}")
        
    async def get_all_user_guilds(cas_username: str | None = None, discord_user_id: int | None = None) -> list[Guild]:
        try:
            logger.debug(f"Getting all guilds for the user {cas_username} {discord_user_id} from the database")
            if cas_username:
            #user = await User.objects.get(discord_id=discord_user_id)
            #user_guilds = user.guilds
                return await User.objects.select_related(User.guilds).get(cas_username=cas_username)
            elif discord_user_id:
                return await User.objects.select_related(User.guilds).get(discord_id=discord_user_id)
            else:
                raise ValueError("Either cas_username or discord_user_id must be provided")
        except Exception as e:
            raise DatabaseError(f"An error occurred while getting all guilds for the user {cas_username}: {e}")





#? ---- not using this : ?

class Database():

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
    
    async def __add_user(user: User):
        try:
            async with AsyncSession(self.async_engine) as session:
                pass
                #await session.commit()
        except Exception as e:
            raise DatabaseError(f"An error occurred while adding the user {user}: {e}")

    async def __get_user(discord_user_id: int | None = None, cas_username: str | None = None) -> User:
        try:
            async with AsyncSession(self.async_engine) as session:
                pass
                #await session.commit()
        except Exception as e:
            raise DatabaseError(f"An error occurred while getting the user {discord_user_id} {cas_username}: {e}")

    async def __delete_user(discord_user_id: int | None = None, cas_username: str | None = None):
        try:
            async with AsyncSession(self.async_engine) as session:
                pass
                #await session.commit()
        except Exception as e:
            raise DatabaseError(f"An error occurred while deleting the user {discord_user_id} {cas_username}: {e}")

    async def __update_user(user: User):
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

app_database = Database()
