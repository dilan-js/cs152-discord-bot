import discord
from discord.ext import commands


class SelectAudience(discord.ui.View):
        def __init__(self, *, timeout: float | None = 180, ):
            super().__init__(timeout=timeout)
            self.selected_audience = None
        @discord.ui.select(custom_id="selection_audience_menu", placeholder="Select your preferred audience", min_values=1, max_values=10,
                           options=([discord.SelectOption(label="18-24 year olds", value="18-24 year olds"), 
                                    discord.SelectOption(label="24-45 year olds", value="24-45 year olds"),
                                    discord.SelectOption(label="45+ years old", value="45+ years old"),
                                    discord.SelectOption(label="Highly engaged users", value="Highly engaged users"),
                                    discord.SelectOption(label="San Francisco Residents", value="San Francisco Residents"),
                                    discord.SelectOption(label="East Bay Residents", value="East Bay Residents"),
                                    discord.SelectOption(label="North Bay Residents", value="North Bay Residents"),
                                    discord.SelectOption(label="South Bay Residents", value="South Bay Residents"),
                                    discord.SelectOption(label="Peninsula Residents", value="Peninsula Residents"),
                                    discord.SelectOption(label="Outer Bay Residents", value="Outer Bay Residents"),
                                    ]))
        async def callback(self, interaction: discord.Interaction, select: discord.ui.Select, custom_id="selection_audience_menu"):
            self.selected_audience = select.values
            # self.cosnfirmed = True
            self.clean_up()
            print("hello")
            await interaction.response.edit_message(view=self)
            # await interaction.response.send_message(f'You selected "{select.values[0]}"! \n I can help with that!')
            # await interaction.followup.send(f'Perfect! You selected "{select.values[0]}"! \n Let us continue creating your ad!')

        def clean_up(self):
            for x in self.children:
                x.disabled = True
            # button.disabled = True
            self.stop()