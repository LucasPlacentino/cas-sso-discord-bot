from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base

class User(Base):
    __tablename__ = "users"

    cas_username: str = Column(String, primary_key=True, unique=True, index=True)
    cas_email: str = Column(String)
    discord_id: int = Column(Integer, unique=True, index=True)
    discord_username: str = Column(String)
    discord_global_name: str = Column(String)
    #TODO: guilds = Column(String) #List[DiscordGuild] ?

    def __repr__(self):
        return f"<User(cas_username={self.cas_username}, discord_id={self.discord_id}, discord_username={self.discord_username}, discord_global_name={self.discord_global_name})>"
