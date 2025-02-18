import logging
from typing import Optional
import disnake
from disnake.ext import commands

from bot import Bot

logger = logging.getLogger("bot")

class RoleManager(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_ready(self):
        """Cache guild roles on startup"""
        logger.info("Role manager ready")
        
    @commands.slash_command()
    @commands.has_permissions(administrator=True)
    async def set_managed_role(self, inter: disnake.ApplicationCommandInteraction, role: disnake.Role):
        """Set the role that will be managed by the bot for this guild"""
        self.bot.guild_roles[inter.guild.id] = role.id
        await inter.response.send_message(
            f"Role {role.name} will now be managed by the bot in this server",
            ephemeral=True
        )

def setup(bot: Bot):
    bot.add_cog(RoleManager(bot))
