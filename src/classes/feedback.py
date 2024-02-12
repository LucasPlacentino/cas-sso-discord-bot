# -*- coding: utf-8 -*-
import logging
from typing import List

import disnake

from bot import Bot


class FeedbackType:
    issue = "problem"
    improve = "enhancement"


class FeedbackModal(disnake.ui.Modal):
    def __init__(self, bot: Bot, type: FeedbackType) -> None:
        self.bot: Bot = bot
        self.type: FeedbackType = type
        components: List[disnake.ui.TextInput] = None
        if type == FeedbackType.issue:
            components = [
                disnake.ui.TextInput(
                    label="Problem",
                    placeholder="What problem did you encounter?",
                    style=disnake.TextInputStyle.paragraph,
                    custom_id="feedback",
                )
            ]
        elif type == FeedbackType.improve:
            components = [
                disnake.ui.TextInput(
                    label="Enhancement",
                    placeholder="What enhancement would you like to see?",
                    style=disnake.TextInputStyle.paragraph,
                    custom_id="feedback",
                )
            ]
        else:
            raise TypeError("arg 'type' should be a 'FeedbackType'.")
        super().__init__(title="Servers registration - Feedback", components=components)

    async def callback(self, interaction: disnake.ModalInteraction, /) -> None:
        await interaction.response.defer(with_message=True, ephemeral=True)
        logging.trace(f"[Feedback] Returning {self.type} feedback by {interaction.author} from {interaction.guild}")
        feedback: str = interaction.text_values.get("feedback")
        if self.type == FeedbackType.issue:
            embed = disnake.Embed(
                title="Feedback - Problem",
                description="> " + "\n> ".join(feedback.splitlines()),
                color=disnake.Color.red(),
            )
        elif self.type == FeedbackType.improve:
            embed = disnake.Embed(
                title="Feedback - Enhancement",
                description="> " + "\n> ".join(feedback.splitlines()),
                color=disnake.Color.teal(),
            )
        embed.add_field(
            name="**__Origin__**",
            value=f"**User :** {interaction.author}\n**Server :** {interaction.guild}\n**Date :** {interaction.created_at.isoformat()}",
        )
        await self.bot.log_channel.send(embed=embed)
        await interaction.edit_original_response(
            embed=disnake.Embed(
                title="Feedback",
                description="Thank you for your feedback!\nIt was successfully sent and will be taken it into account.",
                color=disnake.Color.blue(),
            )
        )
        logging.trace(f"[Feedback] feedback {self.type} by {interaction.author} from {interaction.guild} ended")
