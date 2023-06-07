import discord
from discord.ext import commands


class SelectAction(discord.ui.View):
        def __init__(self, *, timeout: float | None = 180, ):
            super().__init__(timeout=timeout)
            self.selected_value = None
        @discord.ui.select(custom_id="selection_action_menu", placeholder="Select an action for me to do", 
                           options=([discord.SelectOption(label="Report an ad", value="Report an ad", 
                                                          description="See something fishy? Report content here for us to review"), 
                                    discord.SelectOption(label="Create an ad", value="Create an ad",
                                                         description="Want to promote something? Create an ad with us!")]))
        async def callback(self, interaction: discord.Interaction, select: discord.ui.Select, custom_id="selection_action_menu"):
            self.selected_value = select.values[0]
            print(self.selected_value)
            # self.cosnfirmed = True
            self.clean_up()
            await interaction.response.edit_message(view=self)
            # await interaction.response.send_message(f'You selected "{select.values[0]}"! \n I can help with that!')
            # await interaction.followup.send(f'You selected "{select.values[0]}"! \n I can help with that!')

        def clean_up(self):
            for x in self.children:
                x.disabled = True
            # button.disabled = True
            self.stop()