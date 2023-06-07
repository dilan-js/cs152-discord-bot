import discord
from discord.ext import commands
import os
import json
import logging
import re
import requests
from report import Report
import pdb

class ConfirmView(discord.ui.View):
    def __init__(self, *, timeout: float | None = 180, ):
        super().__init__(timeout=timeout)
        self.confirmed = None
    @discord.ui.button(label="Yes", style=discord.ButtonStyle.primary)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button, custom_id="yes"):
        self.confirmed = True
        self.clean_up()
        await interaction.response.edit_message(view=self)
        await interaction.followup.send("You confirmed!")

    @discord.ui.button(label="No", style=discord.ButtonStyle.secondary, custom_id="no")
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = False
        self.clean_up()
        await interaction.response.edit_message(view=self)
        await interaction.followup.send("You confirmed!")

    def clean_up(self):
        for x in self.children:
            x.disabled = True
        # button.disabled = True
        self.stop()