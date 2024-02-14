# -*- coding: utf-8 -*-
import logging
import os

from sqlalchemy.schema import Column
from sqlalchemy.types import String, Integer, Text
from database import Base
from fastapi_discord import Guild as DiscordGuild
from typing import List
from pydantic import BaseModel

from app import get_database_session
from sqlalchemy.orm import Session
from fastapi import Depends


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


class UsersDB(Base):

    __tablename__ = "Users"

    discord_id = Column(Integer, primary_key=True, index=True) # String ? https://github.com/discord/discord-api-docs/blob/main/docs/resources/User.md
    cas_username = Column(Text())
    cas_email = Column(Text())
    discord_username = Column(String(32))
    discord_global_name = Column(Text())
    guilds = Column(Text()) # List of guilds the user is in
