# -*- coding: utf-8 -*-

import asyncio
import os
import logging
import logging.handlers
import platform
import traceback
import tracemalloc
from typing import List

import disnake
from disnake import ApplicationCommandInteraction
from disnake.ext.commands import InteractionBot

#TODO: build bot from https://github.com/bepolytech/ULBDiscordBot

class Bot(InteractionBot):

    def __init__(self, logger, logFormatter):
        self.logger = logger
        self.logFormatter = logFormatter
        self.test_mode = bool(os.getenv("TEST_GUILD"))
        self.cog_not_loaded: List[str] = []

        intents = disnake.Intents.default()
        intents.members = True

        if self.test_mode:
            logging.info("Starting in test mod...")
            super().__init__(intents=intents, test_guilds=[int(os.getenv("TEST_GUILD"))])
        else:
            logging.info("Starting in prod mod...")
            super().__init__(intents=intents)

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
        self.log_channel = self.get_channel(int(os.getenv("LOG_CHANNEL")))
        if not self.log_channel:
            self.log_channel = self.owner.dm_channel
        logging.info("-" * 50)
        logging.info(f"| Logged in as {self.user.name}")
        logging.info(f"| disnake API version: {disnake.__version__}")
        logging.info(f"| Python version: {platform.python_version()}")
        logging.info(f"| Running on: {platform.system()} {platform.release()} ({os.name})")
        logging.info(f"| Owner : {self.owner}")
        logging.info(f"| Cogs loaded : " + ", ".join([f"{cog}" for cog in self.cogs.keys()]))
        if self.cog_not_loaded:
            logging.info("| /!\ Cogs not loaded (see error above): " + ", ".join(self.cog_not_loaded))
        logging.info(f"| Bot Ready !")
        logging.info("-" * 50)

    def load_commands(self) -> None:
        for extension in os.listdir(f"./cogs"):
            if extension.endswith(".py"):
                if extension == ("Admin.py") and not os.getenv("ADMIN_GUILD_ID"):
                    logging.warning("Admin extension skipped because no admin guild set")
                    continue
                try:
                    self.load_extension(f"cogs.{extension[:-3]}")
                    logging.info(f"Loaded extension '{extension[:-3]}'")
                except Exception as e:
                    exception = f"{type(e).__name__}: {e}"
                    logging.warning(
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
        logging.error(
            f"{error} raised on command /{interaction.application_command.name} from {interaction.guild.name+'#'+interaction.channel.name if interaction.guild else 'DM'} by {interaction.author.name}.\n{tb}"
        )

        #Send error msg to the user
        await interaction.send(
            content=self.owner.mention,
            embed=disnake.Embed(
                title=":x: __**ERROR**__ :x:",
                description=f"Une erreur s'est produite lors de la commande **/{interaction.application_command.name}**\n{self.owner.mention} a été prévenu et corrigera ce bug au plus vite !",
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
        logging.trace(
            f"[Bot] Slash command '{interaction.application_command.name}:{interaction.id}' from '{interaction.guild.name+'#'+interaction.channel.name if interaction.guild else 'DM'}' by '{interaction.author.name}' started..."
        )

    async def on_user_command(self, interaction: disnake.UserCommandInteraction) -> None:
        logging.trace(
            f"[Bot] User command '{interaction.application_command.name}:{interaction.id}' from '{interaction.guild.name+'#'+interaction.channel.name if interaction.guild else 'DM'}' by '{interaction.author.name}' started..."
        )

    async def on_message_command(self, interaction: disnake.MessageCommandInteraction) -> None:
        logging.trace(
            f"[Bot] Message command '{interaction.application_command.name}:{interaction.id}' from '{interaction.guild.name+'#'+interaction.channel.name if interaction.guild else 'DM'}' by '{interaction.author.name}' started..."
        )

    async def on_slash_command_error(self, interaction: ApplicationCommandInteraction, error: Exception) -> None:
        await self.send_cmd_error_log(interaction, error)

    async def on_user_command_error(self, interaction: disnake.UserCommandInteraction, error: Exception) -> None:
        await self.send_cmd_error_log(interaction, error)

    async def on_message_command_error(self, interaction: disnake.MessageCommandInteraction, error: Exception) -> None:
        await self.send_cmd_error_log(interaction, error)

    async def on_slash_command_completion(self, interaction: disnake.ApplicationCommandInteraction) -> None:
        logging.trace(
            f"[Bot] Slash command '{interaction.application_command.name}:{interaction.id}' from '{interaction.guild.name+'#'+interaction.channel.name if interaction.guild else 'DM'}' by '{interaction.author.name}' at '{interaction.created_at}' ended normally"
        )

    async def on_user_command_completion(self, interaction: disnake.UserCommandInteraction) -> None:
        logging.trace(
            f"[Bot] User command '{interaction.application_command.name}:{interaction.id}' from '{interaction.guild.name+'#'+interaction.channel.name if interaction.guild else 'DM'}' by '{interaction.author.name}' at '{interaction.created_at}' ended normally"
        )

    async def on_message_command_completion(self, interaction: disnake.MessageCommandInteraction) -> None:
        logging.trace(
            f"[Bot] Message command '{interaction.application_command.name}:{interaction.id}' from '{interaction.guild.name+'#'+interaction.channel.name if interaction.guild else 'DM'}' by '{interaction.author.name}' at '{interaction.created_at}' ended normally"
        )

    #! ----------------TODO:---------------------

    async def _add_role(self, member, role):
        await member.add_roles(role)

    async def add_roles(self, member, role):
        for server in member.servers:
            await self._add_role(member, role)

    #! ----------------TODO:---------------------


