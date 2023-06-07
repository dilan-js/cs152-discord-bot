import discord
from discord.ext import commands


class SelectAdObjective(discord.ui.View):
        def __init__(self, *, timeout: float | None = 180, ):
            super().__init__(timeout=timeout)
            self.selected_ad_objective = None
        @discord.ui.select(custom_id="selection_ad_objective_menu", placeholder="Select your preferred ad objective", 
                           options=([discord.SelectOption(label="Awareness", value="Awareness", 
                                                          description="This is to promote your content to the most people."), 
                                    discord.SelectOption(label="Traffic", value="Traffic",
                                                         description="Increase traffic to your preferred online destination"), 
                                    discord.SelectOption(label="Engagement", value="Engagement",
                                                         description="Target users more likely to engage with your online business"),
                                    discord.SelectOption(label="Leads", value="Leads",
                                                         description="This objective pushes your ad to people willing to share information."),
                                    discord.SelectOption(label="App promotion", value="App promotion",
                                                         description="This objects urges users to install or interact with your app."),
                                    discord.SelectOption(label="Sales", value="Sales",
                                                         description="This objective targets people likely to buy products online!")]))
        async def callback(self, interaction: discord.Interaction, select: discord.ui.Select, custom_id="selection_ad_objective_menu"):
            self.selected_ad_objective = select.values[0]
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