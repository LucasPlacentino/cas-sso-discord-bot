# -*- coding: utf-8 -*-

import disnake
from disnake import ApplicationCommandInteraction
from disnake.ext import commands
from disnake.ext.commands import InteractionBot
import logging
from typing import List
import os
from os import getenv
from dotenv import load_dotenv
load_dotenv()

from ..locales import Locale

import logging.handlers
import platform
import traceback

intents = disnake.Intents.default()
intents.members = True

logger = logging.getLogger("bot")

class Bot(InteractionBot):

    # Singleton pattern
    _instance = None
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
        

    def __init__(self, _logger, _logFormatter, _debug=False):

        self.locale = Locale(debug=_debug)
        self.logger = _logger
        logger = _logger
        self.logFormatter = _logFormatter
        self.test_mode = bool(getenv("TEST_GUILD"))
        self.cog_not_loaded: List[str] = []

        # self.token = getenv("DISCORD_BOT_TOKEN")
        # if not self.token:
        #     logger.error("No discord bot token provided")
        #     raise ValueError("No discord bot token provided")

        if self.test_mode:
            logger.info("Starting Bot in debug mode...")
            super().__init__(intents=intents, test_guilds=[int(getenv("TEST_GUILD"))])
        else:
            logger.info("Starting Bot in prod mode...")
            super().__init__(intents=intents)

        # TODO: rather read database directly?
        self.guild_roles = {}  # Store guild->role mappings ["GuildID": "RoleID"]

        self.load_commands()

    def tracebackEx(self, ex):
        if type(ex) == str:
            return "No valid traceback."
        ex_traceback = ex.__traceback__
        if ex_traceback is None:
            ex_traceback = ex.__traceback__
        tb_lines = [line.rstrip("\n") for line in traceback.format_exception(ex.__class__, ex, ex_traceback)]
        return "".join(tb_lines)
    
    async def on_ready(self) -> None:
        """
        The code in this even is executed when the bot is ready
        """
        self.log_channel = self.get_channel(int(getenv("LOG_CHANNEL")))
        if not self.log_channel:
            self.log_channel = self.owner.dm_channel
        logger.info("-" * 50)
        logger.info(f"| Logged in as {self.user.name}")
        logger.info(f"| disnake API version: {disnake.__version__}")
        logger.info(f"| Python version: {platform.python_version()}")
        logger.info(f"| Running on: {platform.system()} {platform.release()} ({os.name})")
        logger.info(f"| Owner : {self.owner}")
        logger.info(f"| Cogs loaded : " + ", ".join([f"{cog}" for cog in self.cogs.keys()]))
        if self.cog_not_loaded:
            logger.info("| /!\ Cogs not loaded (see error above): " + ", ".join(self.cog_not_loaded))
        logger.info(f"| Bot Ready !")
        logger.info("-" * 50)

    def load_commands(self) -> None:
        for extension in os.listdir(f"./cogs"):
            if extension.endswith(".py"):
                if extension == ("Admin.py") and not getenv("ADMIN_GUILD_ID"):
                    logger.warning("Admin extension skipped because no admin guild set")
                    continue
                try:
                    self.load_extension(f"cogs.{extension[:-3]}")
                    logger.info(f"Loaded extension '{extension[:-3]}'")
                except Exception as e:
                    exception = f"{type(e).__name__}: {e}"
                    logger.warning(
                        f"Failed to load extension {extension[:-3]}: {exception}\n{self.tracebackEx(exception)}"
                    )
                    self.cog_not_loaded.append(extension)

    async def send_error_log(self, tb: str):

        n = len(tb) // 4050

        #Logs need to be diveded into multiple embed due to size limitation
        # TODO Check if we can use a list of embeds and one message
        # TODO Make it dynamic base on the message size from the lib (check library version, maybe need to upgrade)
        for i in range(n):
            await self.log_channel.send(embed=disnake.Embed(description=f"```python\n{tb[4050*i:4050*(i+1)]}```"))
        await self.log_channel.send(embed=disnake.Embed(description=f"```python\n{tb[4050*n:]}```"))

    async def send_cmd_error_log(self, interaction: ApplicationCommandInteraction, error: Exception):
        tb = self.tracebackEx(error)
        logger.error(
            f"{error} raised on command /{interaction.application_command.name} from {interaction.guild.name+'#'+interaction.channel.name if interaction.guild else 'DM'} by {interaction.author.name}.\n{tb}"
        )

        #Send error msg to the user
        await interaction.send(
            content=self.owner.mention,
            embed=disnake.Embed(
                title=":x: __**ERROR**__ :x:",
                description=f"An Error occurred when executing the command**/{interaction.application_command.name}**\n{self.owner.mention} was notified et will fix this bug asap!",
                color=disnake.Colour.red(),
            ),
            delete_after=10,
        )

        #Send logs to admins
        await self.log_channel.send(
            embed=disnake.Embed(title=f":x: __** ERROR**__ :x:", description=f"```{error}```").add_field(
                name=f"Raised on command :",
                value=f"**/{interaction.application_command.name}:{interaction.id}** from {interaction.guild.name+'#'+interaction.channel.name if interaction.guild else 'DM'} by {interaction.author.mention} at {interaction.created_at} with options\n```{interaction.filled_options}```"
                + (f" and target\n``'{interaction.target}``'." if interaction.target else "."),
            )
        )
        await self.send_error_log(tb)

    async def on_slash_command(self, interaction: disnake.ApplicationCommandInteraction) -> None:
        logger.trace(
            f"[Bot] Slash command '{interaction.application_command.name}:{interaction.id}' from '{interaction.guild.name+'#'+interaction.channel.name if interaction.guild else 'DM'}' by '{interaction.author.name}' started..."
        )

    async def on_user_command(self, interaction: disnake.UserCommandInteraction) -> None:
        logger.trace(
            f"[Bot] User command '{interaction.application_command.name}:{interaction.id}' from '{interaction.guild.name+'#'+interaction.channel.name if interaction.guild else 'DM'}' by '{interaction.author.name}' started..."
        )

    async def on_message_command(self, interaction: disnake.MessageCommandInteraction) -> None:
        logger.trace(
            f"[Bot] Message command '{interaction.application_command.name}:{interaction.id}' from '{interaction.guild.name+'#'+interaction.channel.name if interaction.guild else 'DM'}' by '{interaction.author.name}' started..."
        )

    async def on_slash_command_error(self, interaction: ApplicationCommandInteraction, error: Exception) -> None:
        await self.send_cmd_error_log(interaction, error)

    async def on_user_command_error(self, interaction: disnake.UserCommandInteraction, error: Exception) -> None:
        await self.send_cmd_error_log(interaction, error)

    async def on_message_command_error(self, interaction: disnake.MessageCommandInteraction, error: Exception) -> None:
        await self.send_cmd_error_log(interaction, error)

    async def on_slash_command_completion(self, interaction: disnake.ApplicationCommandInteraction) -> None:
        logger.trace(
            f"[Bot] Slash command '{interaction.application_command.name}:{interaction.id}' from '{interaction.guild.name+'#'+interaction.channel.name if interaction.guild else 'DM'}' by '{interaction.author.name}' at '{interaction.created_at}' ended normally"
        )

    async def on_user_command_completion(self, interaction: disnake.UserCommandInteraction) -> None:
        logger.trace(
            f"[Bot] User command '{interaction.application_command.name}:{interaction.id}' from '{interaction.guild.name+'#'+interaction.channel.name if interaction.guild else 'DM'}' by '{interaction.author.name}' at '{interaction.created_at}' ended normally"
        )

    async def on_message_command_completion(self, interaction: disnake.MessageCommandInteraction) -> None:
        logger.trace(
            f"[Bot] Message command '{interaction.application_command.name}:{interaction.id}' from '{interaction.guild.name+'#'+interaction.channel.name if interaction.guild else 'DM'}' by '{interaction.author.name}' at '{interaction.created_at}' ended normally"
        )

    async def add_role_to_user(self, guild_id: int, user_id: int, role_id: int) -> bool:
        """Add a role to a user in a specific guild"""
        try:
            guild = self.get_guild(guild_id)
            if not guild:
                logger.error(f"Guild {guild_id} not found")
                return False
                
            guild_member = guild.get_member(user_id)
            if not guild_member:
                logger.error(f"Member {user_id} not found in guild {guild_id}")
                return False
                
            role = guild.get_role(role_id)
            if not role:
                logger.error(f"Role {role_id} not found in guild {guild_id}")
                return False
                
            await guild_member.add_roles(role)
            logger.info(f"Added role {role.name} to user {guild_member.name} in {guild.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding role: {e}")
            return False
            
    async def remove_role_from_user(self, guild_id: int, user_id: int, role_id: int) -> bool:
        """Remove a role from a user in a specific guild"""
        try:
            guild = self.get_guild(guild_id)
            if not guild:
                logger.error(f"Guild {guild_id} not found")
                return False
                
            guild_member = guild.get_member(user_id)
            if not guild_member:
                logger.error(f"Member {user_id} not found in guild {guild_id}") 
                return False
                
            role = guild.get_role(role_id)
            if not role:
                logger.error(f"Role {role_id} not found in guild {guild_id}")
                return False
                
            await guild_member.remove_roles(role)
            logger.info(f"Removed role {role.name} from user {guild_member.name} in {guild.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing role: {e}")
            return False


"""
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.slash_command(description="Say hello!")
async def hello(inter):
    await inter.response.send_message("Hello, world!")
"""


#bot.run('YOUR_BOT_TOKEN')