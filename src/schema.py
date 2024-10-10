from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base

#! ----------------------------
#! NOT NECESSARY IF USING ORMAR
#! ----------------------------

"""

user_guild_association = Table(
    "user_guilds",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("guild_id", Integer, ForeignKey("guilds.id")),
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    cas_username: str = Column(String, unique=True, index=True, nullable=False)
    cas_email: str = Column(String)
    discord_user_id: int = Column(Integer, unique=True, index=True, nullable=False)
    discord_username: str = Column(String)
    discord_global_name: str = Column(String)
    #TODO: guilds = Column(String) #List[DiscordGuild] ?
    guilds = relationship(
        "Guild",
        secondary=user_guild_association,
        back_populates="users"
    )

    def __repr__(self):
        return f"<User(cas_username={self.cas_username}, discord_id={self.discord_id}, discord_username={self.discord_username}, discord_global_name={self.discord_global_name})>"
    
class Guild(Base):
    __tablename__ = "guilds"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    discord_guild_id: int = Column(Integer, unique=True, index=True, nullable=False)
    guild_name: str = Column(String)
    users = relationship(
        "User",
        secondary=user_guild_association,
        back_populates="guilds"
    )

    def __repr__(self):
        return f"<Guild(discord_id={self.discord_id}, discord_name={self.discord_name})>"
"""
