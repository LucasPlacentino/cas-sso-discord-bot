# -*- coding: utf-8 -*-
import logging
from os import getenv
from dotenv import load_dotenv
load_dotenv()

DEBUG = True if getenv("DEBUG") is not None and getenv("DEBUG") != "" else False

from .database import Base
from fastapi_discord import Guild as DiscordGuild
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from .app import get_database_session
#from sqlalchemy.orm import Session, relationship
#from sqlalchemy.schema import Column
#from sqlalchemy.types import String, Integer, Text
import ormar # based on SQLAlchemy Core so works with Alembic
from database import Database as db
from database import base_ormar_config
from fastapi import Depends

#TODO: use ormar ?

logger = logging.getLogger("models")
if DEBUG:
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

#class MainMeta(ormar.ModelMeta):
#    metadata = sqlalchemy.metadata
#    database = db

class Guild(ormar.Model): #! also inherit from DiscordGuild (from Disnake) ?
    #ormar.config = db.ormar_base_config
    ormar.config = base_ormar_config.copy(tablename="guilds")

    db_id: int = ormar.Integer(primary_key=True, autoincrement=True, index=True, unique=True)
    discord_guild_id: int = ormar.Integer(index=True, unique=True, nullable=False)
    guild_name: str = ormar.String(max_length=102) # max length of a guild name is 100 characters (excluding trailing and meading whitespaces)
    added_at: datetime = ormar.DateTime(server_default=ormar.func.now())

    async def save(self):
        if DEBUG:
            logger.debug(f"Saving guild {self.guild_name} to database")
        await super().save()

class User(ormar.Model): #! also inherit from DiscordUser (from Disnake) ?
    #ormar.config = db.ormar_base_config
    ormar.config = base_ormar_config.copy(tablename="users")
    #class Meta(MainMeta):
    #    tablename = "users"

    db_id: int = ormar.Integer(primary_key=True, autoincrement=True, index=True, unique=True)
    cas_username: str = ormar.String(max_length=10, unique=True, index=True, nullable=False)
    cas_email: str = ormar.String(max_length=255, unique=True, index=True)
    discord_id: int = ormar.Integer(index=True, unique=True, nullable=False)
    discord_username: str = ormar.String(max_length=33, index=True, nullable=True) # max length of a discord username is 32 characters, one extra just in case
    discord_global_name: str = ormar.String(max_length=33, nullable=True) # max length of a discord global name is 32 characters, one extra in case of @ char returned by api
    added_at: datetime = ormar.DateTime(server_default=ormar.func.now())

    # Relationship with Guild (many-to-many) :
    #guilds: Optional[List[DiscordGuild]] = ormar.ManyToMany(DiscordGuild, through="UserGuild")
    guilds: List[Guild] = ormar.ManyToMany(Guild, skip_reverse=True) # can be empty on User creation, skip_reverse=True because guilds do not need to know about users

    async def save(self):
        if DEBUG:
            logger.debug(f"Saving user {self.cas_username} to database")
        await super().save()




# ------------------------------

class User(BaseModel):
    cas_username: str
    cas_email: str
    discord_id: int
    discord_username: str
    discord_global_name: str
    guilds: List[DiscordGuild]
    
    def __init__(self, cas_username, cas_email, discord_id = None, discord_username = None, discord_global_name = None, guilds: List[DiscordGuild] = []):
        self.cas_username = cas_username
        self.cas_email = cas_email
        self.discord_id = discord_id
        self.discord_username = discord_username
        self.discord_global_name = discord_global_name
        self.guilds = guilds

    async def link_accounts(self, db: Session = Depends(get_database_session)):
        #user = db.query(UsersDB).get(self.cas_username)
        user = await db.query(UsersDB).filter(UsersDB.cas_username == self.cas_username).first()
        user.discord_id = self.discord_id
        user.discord_username = self.discord_username
        user.discord_global_name = self.discord_global_name
        user.guilds = self.guilds
        await db.commit()
        await db.refresh(user)
        pass # TODO: add to database

    async def unlink_accounts(self, db: Session = Depends(get_database_session)):
        #user = db.query(UsersDB).get(self.cas_username)
        user = await db.query(UsersDB).filter(UsersDB.cas_username == self.cas_username).first()
        user.discord_id = None
        user.discord_username = None
        user.discord_global_name = None
        user.guilds = None
        await db.commit()
        await db.refresh(user)
        pass #TODO: remove discord info from database

    async def delete_from_db(self, db: Session = Depends(get_database_session)):
        #user = db.query(UsersDB).get(self.cas_username)
        user = await db.query(UsersDB).filter(UsersDB.cas_username == self.cas_username).first()
        await db.delete(user)
        await db.commit()
        pass #TODO: completely remove user from database

    def give_role(self, db: Session = Depends(get_database_session)):
        pass # TODO: add to discord

    def __str__(self):
        return f"User: {self.cas_username}, Discord ID: {self.discord_id}"
    
    class Config:
        orm_mode = True

"""

class Guild(BaseModel, DiscordGuild):
    #TODO: idk

    class Config:
        orm_mode = True

#class UsersDB(Base, User, DiscordUser): #! use multiple inheritance ?
#class UserDB(SQLModel, table=True): #! ? SQLModel
class UsersDB(Base):

    __tablename__ = "Users"

    discord_id = Column(Integer, primary_key=True, unique=True, index=True) # String ? https://github.com/discord/discord-api-docs/blob/main/docs/resources/User.md #! TODO: shouldnt use discord_id as primary key in case Discord changes them (low chance tho)
    cas_username = Column(String, unique=True, index=True)
    cas_email = Column(String, unique=True, index=True)
    discord_username = Column(String(32), unique=True, index=True)
    discord_global_name = Column(String)
    guilds = Column(String) # List of guilds the user is in

    #guilds = relationship("GuildsDB", back_populates="users") #?

    class Config:
        orm_mode = True

class GuildsDB(Base):
    
    __tablename__ = "Guilds"

    guild_id = Column(Integer, primary_key=True, unique=True, index=True)

    #users = relationship("UsersDB", back_populates="guilds") # ?

    class Config:
        orm_mode = True

"""
