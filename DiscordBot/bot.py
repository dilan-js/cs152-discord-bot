# bot.py
import discord
from discord.ext import commands
import os
import json
import logging
import re
import requests
from report import Report
from review import Review
from report import State
import pdb

 # Set up logging to the console
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# There should be a file called 'tokens.json' inside the same folder as this file
token_path = 'tokens.json'
if not os.path.isfile(token_path):
    raise Exception(f"{token_path} not found!")
with open(token_path) as f:
    # If you get an error here, it means your token is formatted incorrectly. Did you put it in quotes?
    tokens = json.load(f)
    discord_token = tokens['discord']


class ModBot(discord.Client):
    def __init__(self): 
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='.', intents=intents)
        self.group_num = None
        self.mod_channels = {} # Map from guild to the mod channel id for that guild
        self.reports = {} # Map from user IDs to the state of their report

        self.reviews = [] # Dictionary of Reports to Review
        self.info = {"reporters":{}, "advertisers":{}} # Dictionary of tracked values
        self.current_review = None

    async def on_ready(self):
        print(f'{self.user.name} has connected to Discord! It is these guilds:')
        for guild in self.guilds:
            print(f' - {guild.name}')
        print('Press Ctrl-C to quit.')

        # Parse the group number out of the bot's name
        match = re.search('[gG]roup (\d+) [bB]ot', self.user.name)
        if match:
            self.group_num = match.group(1)
        else:
            raise Exception("Group number not found in bot's name. Name format should be \"Group # Bot\".")

        # Find the mod channel in each guild that this bot should report to
        for guild in self.guilds:
            for channel in guild.text_channels:
                if channel.name == f'group-{self.group_num}-mod':
                    self.mod_channels[guild.id] = channel
        

    async def on_message(self, message):
        '''
        This function is called whenever a message is sent in a channel that the bot can see (including DMs). 
        Currently the bot is configured to only handle messages that are sent over DMs or in your group's "group-#" channel. 
        '''
        
        # Ignore messages from the bot 
        if message.author.id == self.user.id:
            return

        # Check if this message was sent in a server ("guild") or if it's a DM
        if message.guild:
            #check if perpetrator is in a reports class instance 
            # COME BACK
            # for reporter, report in self.reports.items():
            #     if report.PERP_INFO["author_id"] == message.author.id:
            #         # this person has been reported by a user in this channel
            #         # prevent this person from messaging until mod team figures out what to do
            #         await message.delete()
            #         return await message.channel.send(f"You can't do that, {message.author.mention}")
                
            await self.handle_channel_message(message)
        else:
            await self.handle_dm(message)

    async def handle_dm(self, message):
        # Handle a help message
        if message.content == Report.HELP_KEYWORD:
            reply =  "Use the `report` command to begin the reporting process.\n"
            reply += "Use the `cancel` command to cancel the report process.\n"
            await message.channel.send(reply)
            return

        author_id = message.author.id
        responses = []

        # Only respond to messages if they're part of a reporting flow
        if author_id not in self.reports and not message.content.startswith(Report.START_KEYWORD):
            return

        # If we don't currently have an active report for this user, add one
        if author_id not in self.reports:
            new_report = Report(self)
            reports_per_author = []
            reports_per_author.append(new_report)
            self.reports[author_id] = reports_per_author
            self.reports[author_id] = Report(self)
        # else:
        #     #we do have an active report!!! 
        #     # DILAN COME BACK TO THIS
        #     return
        # Let the report class handle this message; forward all the messages it returns to uss
        responses = await self.reports[author_id].handle_message(message)
        CURRENT_REPORT = self.reports[author_id]

        if CURRENT_REPORT.state == State.REPORT_CANCELLED:
            #write to database
            print("report cancelled")

        for r in responses:
            await message.channel.send(r)


        # print("THIS IS CURRENT REPORT.state" , CURRENT_REPORT.state)
        # if CURRENT_REPORT.state == State.MESSAGE_IDENTIFIED:
        #     print("STiha;lefh;aelfh")
        #     view = ConfirmView()
        #     await message.channel.send(view=view)
        #     await view.wait()

        # view = Confirm_View()
        # If the report is complete or cancelled, remove it from our map
        if self.reports[author_id].state == State.REPORT_CANCELLED:
            self.reports[author_id].report_cancelled()
            self.reports.pop(author_id)
        elif self.reports[author_id].state == State.REPORT_COMPLETE:
            curr_report = self.reports[author_id]
            print(curr_report.reported_user_info, curr_report.report_type, curr_report.report_reason, curr_report.report_clarity_reason, curr_report.handle_reported_user, curr_report.reporter)
            
            # print(curr_report["reporter"]["previous_reports"])
            # prev_reports =  curr_report["reporter"]["previous_reports"]
            # if len(prev_reports) == 0:
            #     prev_reports = []
            #     prev_reports.append(self.reports[author_id])
            #     curr_report["reporter"]["previous_reports"] = prev_reports
            # else:
            #     prev_reports.append(self.reports[author_id])
            self.reports[author_id].report_complete(curr_report)
            # ADD TO DB!
            self.reviews.append([author_id, self.reports[author_id]])

            # Add to info on Reports
            if author_id not in self.info["reporters"]:
                self.info["reporters"][author_id] = {"reported":1, "false":0}
            else:
                self.info["reporters"][author_id]["reported"] += 1

            # Add to info on Advertisers
            if self.reports[author_id].reported_user_info["author_id"] not in self.info["advertisers"]:
                self.info["advertisers"][self.reports[author_id].reported_user_info["author_id"]] = {"reported":1, "false":0}
            else:
                self.info["advertisers"][self.reports[author_id].reported_user_info["author_id"]]["reported"] += 1

            
            # Get Mod Channel
            # mod_channel = None
            # for channel_name in self.mod_channels:
                # if self.mod_channels[channel_name].name == f'group-{self.group_num}-mod':
                    # mod_channel = self.mod_channels[channel_name]
            
            # Send Message to Mod Channel on new report
            # await mod_channel.send(f'New Reported Ad: {self.reviews[0][0]}: "{self.reviews[0][1].PERP_INFO}"\n Advertiser: {self.info["advertisers"][self.reports[author_id].PERP_INFO["author_id"]]} \n Reporter: {self.info["reporters"][author_id]}')

            self.reports.pop(author_id)
        

    async def handle_channel_message(self, message):
        # handle messages sent in the "group-#" channel
        if message.channel.name == f'group-{self.group_num}':
            # Forward the message to the mod channel
            # mod_channel = self.mod_channels[message.guild.id]
            # await mod_channel.send(f'Forwarded message:\n{message.author.name}: "{message.content}"')
            # scores = self.eval_text(message.content)
            # await mod_channel.send(self.code_format(scores))
            return
        
        elif message.channel.name == f'group-{self.group_num}-mod':
            # Handle a help message
            if message.content == Review.HELP_KEYWORD:
                reply =  "Use the `review` command to begin reviewing the top priority reported ad\n"
                reply += "Use the `cancel` command to cancel the review process.\n"
                await message.channel.send(reply)
                return
            
            # Message is not help
            if self.current_review == None:

                if len(self.reviews) > 0:
                    self.current_review = Review(self, self.reviews[0], self.info["advertisers"][self.reviews[0][1].reported_user_info["author_id"]], self.info["reporters"][self.reviews[0][0]])
                else:
                    await message.channel.send("There are no reported ads in the queue")
                    return

            responses = await self.current_review.handle_message(message)

            for r in responses:
                await message.channel.send(r)

            if self.current_review.state == State.REVIEW_CANCELLED:
                self.current_review = None

            elif self.current_review.report_complete():
                if self.current_review.final_state == 0:
                    self.info["advertisers"][self.reviews[0][1].reported_user_info["author_id"]]["false"] += 1

                if self.current_review.final_state == 1:
                    self.info["advertisers"][self.reviews[0][1].reported_user_info["author_id"]]["false"] += 1
                    
                if self.current_review.final_state == 2:
                    self.info["reporters"][self.reviews[0][0]]["false"] += 1

                if self.current_review.final_state == 3:
                    self.info["reporters"][self.reviews[0][0]]["false"] += 1

                self.reviews.pop(0)
                self.current_review = None
            return
        
        else:
            return

    
    def eval_text(self, message):
        ''''
        TODO: Once you know how you want to evaluate messages in your channel, 
        insert your code here! This will primarily be used in Milestone 3. 
        '''
        return message

    
    def code_format(self, text):
        ''''
        TODO: Once you know how you want to show that a message has been 
        evaluated, insert your code here for formatting the string to be 
        shown in the mod channel. 
        '''
        return "Evaluated: '" + text+ "'"

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
            await interaction.followup.send("You did not confirm. Please try again.")
        
        def clean_up(self):
            for x in self.children:
                x.disabled = True
            # button.disabled = True
            self.stop()
client = ModBot()
client.run(discord_token)


