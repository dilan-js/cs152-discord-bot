# bot.py
import discord
from discord.ext import commands
import os
import json
import logging
import re
import requests
from report import Report
from ad import Ad
from ad import AD_STATE
from review import Review
from report import State
import pdb
from tinydb import TinyDB, Query
from views import ConfirmView
from views import SelectAction
from views import SelectAdObjective, SelectAudience
# from automation import Automation
import traceback

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

    REPORT_PRIORITY = {"ron desantis' presidential campaign":3,
                       "donald trump trials":1,
                       "conflict between russia and ukraine":2,
                       "covid or vaccinations":4,}
    
    LABELS = ["Election", "COVID", "Other"]


    def __init__(self): 
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='.', intents=intents)
        self.group_num = None
        self.mod_channels = {} # Map from guild to the mod channel id for that guild
        self.reports = {} # Map from user IDs to the state of their report
        self.current_review = None
        self.current_report = None
        self.ads = {}
        self.ad_author_id = None
        self.advertiser = {"author_id": None, "author_name": None, "ad_id": None, "channel_id": None}
        self.db = TinyDB('db.json')
        self.usersDB = TinyDB('users.json')
        self.reviewDB = TinyDB('reviewQueue.json')
        self.does_user_want_to_report = False
        self.does_user_want_to_ad = False
        self.User = None
        self.review_queue = []

        # self.autoBot = Automation()

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
        
        self.User = Query()
        result = self.reviewDB.get(self.User['review_queue'].exists())
        if result == None:
            self.reviewDB.insert({'review_queue': self.review_queue})
        else:
            self.review_queue = result['review_queue']

    
    async def send_channel_message(self, channel_id, message_text):
        try:
            channel = await self.fetch_channel(channel_id)
            await channel.send(message_text)
        except:
            pass

    async def dm_user(self, user_id, message_text):
        try:
            user = await self.fetch_user(user_id)
            dm_channel = await user.create_dm()
            await dm_channel.send(message_text)
        except:
            pass
    
    async def delete_message(self, channel_id, message_id):
        try:
            channel = await self.fetch_channel(channel_id)
            message = await channel.fetch_message(message_id)
            await message.delete()
        except:
            pass

    async def block_user(self, user_id):
        self.usersDB.update({"ad-block": 1}, self.User["author_id"] == user_id)

    async def ban_user(self, user_id):
        self.usersDB.update({"ad-ban": 1}, self.User["author_id"] == user_id)

    async def ban_user_reports(self, user_id):
        self.usersDB.update({"report-ban": 1}, self.User["author_id"] == user_id)

    async def update_user_database_report(self, report, confidence=0.9):
        # Add to info on Reports
        if not self.usersDB.contains(self.User["author_id"] == report.reporter["author_id"]):
            self.usersDB.insert({"author_id": report.reporter["author_id"], "user-report":1, "user-false":0, "report-ban":0, "ad-report":0, "ad-false":0, "ad-ban": 0, "ad-block": 0, "ban": 0, "confidence": confidence})
        else:
            user_info = self.usersDB.get(self.User["author_id"] == report.reporter["author_id"])
            userReport = user_info["user-report"] + 1
            self.usersDB.update({"user-report": userReport}, self.User["author_id"] == report.reporter["author_id"])
        # Add to info on Advertisers
        if not self.usersDB.contains(self.User["author_id"] == report.reported_user_info["author_id"]):
            self.usersDB.insert({"author_id": report.reported_user_info["author_id"], "user-report":0, "user-false":0, "report-ban":0, "ad-report":1, "ad-false":0, "ad-ban": 0, "ad-block": 0, "ban": 0, "confidence": confidence})
        else:
            user_info = self.usersDB.get(self.User["author_id"] == report.reported_user_info["author_id"])
            adReport = user_info["ad-report"] + 1
            self.usersDB.update({"ad-report": adReport}, self.User["author_id"] == report.reported_user_info["author_id"])
    
    async def update_user_database_review(self, review, report):
        reporter_info = self.usersDB.get(self.User["author_id"] == report["reporter"]["author_id"])
        reported_info = self.usersDB.get(self.User["author_id"] == report["reported_user"]["author_id"])
        # Bad ad w/ history
        if review.final_state == 0:
            adFalse = reported_info["ad-false"] + 1
            self.usersDB.update({"ad-false": adFalse}, self.User["author_id"] == report["reported_user"]["author_id"])
        # Bad ad w/o histrory
        elif review.final_state == 1:
            adFalse = reported_info["ad-false"] + 1
            self.usersDB.update({"ad-false": adFalse}, self.User["author_id"] == report["reported_user"]["author_id"])
        # Bad report w/ history
        elif review.final_state == 2:
            reportFalse = reporter_info["user-false"] + 1
            self.usersDB.update({"user-false": reportFalse}, self.User["author_id"] == report["reporter"]["author_id"])
        # Bad report w/o histrory
        elif review.final_state == 3:
            reportFalse = reporter_info["user-false"] + 1
            self.usersDB.update({"user-false": reportFalse}, self.User["author_id"] == report["reporter"]["author_id"])
    
    async def add_report_to_queue(self, report, id):
        # Get Basic Info On Report
        report_message_id = report.reported_user_info['message_id']
        report_cat = report.report_clarity_reason
        report_type = report.report_reason

        report_priority = 0
        if report_cat in self.REPORT_PRIORITY.keys():
            report_priority = self.REPORT_PRIORITY[report_cat]

        # Find Location to Insert
        insert_location = 0
        for id_iter in range(len(self.review_queue)):
            report_iter = self.db.get(self.User["id"] == self.review_queue[id_iter])
            iter_cat = report_iter['report']['report_clarity_reason']
            iter_type = report_iter['report']["report_reason"]

            # Check for Duplicate Report
            iter_message_id = report_iter['reported_user']['message_id']
            if report_message_id == iter_message_id:
                return
            
            # Check for Priortity Cat
            if iter_cat in self.REPORT_PRIORITY.keys():
                iter_priority = self.REPORT_PRIORITY[iter_cat]
                if report_priority > iter_priority:
                    break
            
            # Update location and continue
            insert_location = id_iter + 1
        
        # Insert into Queue and update DB
        self.review_queue.insert(insert_location, id)
        self.reviewDB.update({'review_queue': self.review_queue}, self.User['review_queue'].exists())

    async def remove_report_from_queue(self, id):
        self.review_queue.remove(id)
        self.reviewDB.update({'review_queue': self.review_queue}, self.User['review_queue'].exists())

    async def add_message_to_db_bot(self, message, report_cat, confidence):
        bot_report = Report(self)
        bot_report.report_type = "Misinformation/Disinformation"
        bot_report.report_reason = "Untrue/False"
        bot_report.report_clarity_reason = report_cat
        bot_report.handle_reported_user = "Do Nothing"

        bot_report.reported_user_info = {"author_id": message.author.id, "author_name":  message.author.name, "message_id": message.id, "message_content": message.content, "channel_id": message.channel.id}
        bot_report.reporter = {"author_id": 0, "author_name": "Bot", "message_id": 0, "channel_id": 0}

        await self.update_user_database_report(bot_report, confidence)

        id = bot_report.report_complete()
        await self.add_report_to_queue(bot_report, id)

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
            # Proceed to Channel Flow
            await self.handle_channel_message(message)
        else:
            # Proceed to DM Flow
            await self.handle_dm(message)


    async def handle_dm(self, message):
        does_user_want_to_report = False
        does_user_want_to_create_ad = False
        author_id = message.author.id
        # Handle a help message
        if message.content == Report.HELP_KEYWORD:
            reply =  "Hi! How can I help?\n"
            reply += "Use the select menu below to indicate what you would like to do.\n"
            reply += "You can also type `cancel` anytime to cancel all actions.\n"
            # reply += "Use the `cancel` command to cancel the report process.\n"
            view = SelectAction.SelectAction()
            await message.channel.send(reply)
            await message.channel.send(view=view)
            await view.wait()
            if view.selected_value == 'Create an ad':
                self.does_user_want_to_report = False
                self.does_user_want_to_ad = True
                await message.channel.send("Awesome! You want to create an ad.")
            elif view.selected_value == "Report an ad":
                self.does_user_want_to_report = True
                self.does_user_want_to_ad = False
            # print("THIS ISI SELECE DVALUE = " , view.selected_value)
            # return
            
        if self.does_user_want_to_ad:
            #handle cancelling
            self.ad_author_id = message.author.id
            if message.content == Ad.CANCEL_KEYWORD:
                responses = await self.ads[self.ad_author_id].handle_message(message)
                for r in responses:
                    await message.channel.send(r)
                print("WE ARE POPPING")
                self.ads.pop(self.ad_author_id)
            #check that there is no existing ad for review
            if self.ad_author_id not in self.ads:
                new_ad = Ad(self)
                print("WE ARE ADDING")
                self.advertiser["author_id"] = message.author.id
                self.advertiser["author_name"] = message.author.name
                self.advertiser["channel_id"] = message.channel.id
                self.ads[self.ad_author_id] = new_ad 
            # elif  self.ad_author_id  in self.ads
            #when a usre submits for review, they should not be able to submit another ad
            #ad under review means ad is in database, not in self.ads datastructre
            # else:
            #     reply =  "Oh no!\n"
            #     reply += "It seems you have already submitted an advertisement for review.\n"
            #     reply += "Until that advertisement is reviewed, we cannot deploy another ad.\n"
            #     reply += "We're very sorry. Please have a good day! Goodbye\n"
            #     await message.channel.send(reply)
            #     return
                
            #get their objectives
            if self.ads[self.ad_author_id].state == AD_STATE.AD_START:
                reply =  "On to the next step!\n"
                reply += "Use the select menu to pick an objective for your ad.\n"
                reply += "You can also type `cancel` anytime to cancel all actions.\n"
                await message.channel.send(reply)
                view = SelectAdObjective.SelectAdObjective()
                
                await message.channel.send(view=view)
                await view.wait()
                user_objective_selection = view.selected_ad_objective.lower()
                if user_objective_selection in Ad.OBJECTIVE_OPTIONS:
                    responses = await self.ads[self.ad_author_id].handle_message(user_objective_selection)
                    should_cancel = False
                    for r in responses:
                        if 'Sorry' in r or 'sorry' in r:
                            self.ads.pop(self.ad_author_id)
                            should_cancel = True
                        await message.channel.send(r)
                    if should_cancel:
                        return
            
            if self.ads[self.ad_author_id].state == AD_STATE.AD_OBJECTIVE_SELECTED:
                #user made successful objective selection
                #create audience 
                print("HIi")
                view = SelectAudience.SelectAudience()
                
                await message.channel.send(view=view)
                await view.wait()
                user_audience_selections = view.selected_audience
                user_audience_selections = [selection.lower() for selection in user_audience_selections]
                if set(user_audience_selections).issubset(set(Ad.AUDIENCE_OPTIONS)):
                    responses = await self.ads[self.ad_author_id].handle_message(user_audience_selections)
                    should_cancel = False
                    for r in responses:
                        if 'Sorry' in r or 'sorry' in r:
                            self.ads.pop(self.ad_author_id)
                            should_cancel = True
                        await message.channel.send(r)
                    if should_cancel:
                        return
                return        
            if self.ads[self.ad_author_id].state == AD_STATE.AUDIENCE_IDENTIFIED:
                # directions = "Type in the title of the ad you want to create.\n"
                # directions += "If you would like to cancel at anytime, type `cancel` to exit."
                # await message.channel.send(directions)
                print("dilan IN AUDIENCE IDENTIFIED, TITLE = ", message.content)
                #user made successful objective selection
                #create audience 
                user_title = message.content
                responses = await self.ads[self.ad_author_id].handle_message(user_title)
                for r in responses:
                    if 'Sorry' in r or 'sorry' in r:
                        self.ads.pop(self.ad_author_id)
                    await message.channel.send(r)
                return
            
            if self.ads[self.ad_author_id].state == AD_STATE.AD_TITLE_CONFIGURED:
                #user made successful objective selection
                #create audience 
                
                responses, current_ad = await self.ads[self.ad_author_id].handle_message(message.content)
                

                should_cancel = False
                for r in responses:
                    if 'Sorry' in r or 'sorry' in r:
                        self.ads.pop(self.ad_author_id)
                        should_cancel = True
                    await message.channel.send(r)
                if should_cancel:
                    return
                
                embed = discord.Embed(title=current_ad["title"], description=current_ad["content"])
                await message.channel.send(embed=embed)
                print(current_ad)



            
            

        # Check if the Sender is Banned from reporting
        try:
            author_info = self.usersDB.get(self.User["author_id"] == message.author.id)
        except:
            author_info = None
        
        if author_info is not None:
            if author_info["report-ban"] == 1:
                await self.dm_user(message.author.id, "Your account has been banned from reporting due to a history of false reports")
                return

        author_id = message.author.id
        responses = []

        # Only respond to messages if they're part of a reporting flow
        if author_id not in self.reports and not message.content.startswith(Report.START_KEYWORD):
            reply =  "You do not have an active report in progress.\n"
            reply += "Use the `help` command to learn about your options.\n"
            await message.channel.send(reply)
            return

        # If we don't currently have an active report for this user, add one
        if author_id not in self.reports:
            new_report = Report(self)
            self.reports[author_id] = new_report
        
        # Hand Next Step in Reporting Flow
        responses = await self.reports[author_id].handle_message(message)
        current_report = self.reports[author_id]
        
        # Send Responses to User
        for r in responses:
            await message.channel.send(r)

        # view = Confirm_View()
        # If the report is complete or cancelled, remove it from our map
        if current_report.state == State.REPORT_CANCELLED:
            current_report.report_cancelled()
            self.reports.pop(author_id)

        elif current_report.state == State.REPORT_COMPLETE:
            id = current_report.report_complete()
            # ADD TO DB!
            
            # Update Reports Queue
            await self.add_report_to_queue(current_report, id)

            # Update User Database
            await self.update_user_database_report(current_report)
            
            # Handle if the User Blocks the advertiser
            if current_report.handle_reported_user == 'block':
                print("Blocking")
                await self.block_user(current_report.reported_user_info["author_id"])

            self.reports.pop(author_id)
        

    async def handle_channel_message(self, message):
        
        # handle messages sent in the "group-#" channel
        if message.channel.name == f'group-{self.group_num}':
            # Check if the Sender is Banned or Blocked
            try:
                author_info = self.usersDB.get(self.User["author_id"] == message.author.id)
            except:
                author_info = None
            if author_info is not None:
                if author_info["ad-ban"] == 1:
                    await self.dm_user(message.author.id, "Your account has been banned due to a history of misinformation, You cannot post")
                    await self.delete_message(message.channel.id, message.id)

                    return
                elif author_info["ad-block"] == 1:
                    await self.delete_message(message.channel.id, message.id)
                    # No dm, since only blocked by this user

                    # normally wouldn't but since we are just considering one person's feed no need to 
                    return

            # Send Message to Automated Review
            try:
                print("hey") #COMMENT BACK IN BELOW CODE FOR SERVER
                # text_classification = self.autoBot.classify(message.content)
                # text_category = self.autoBot.categorize(message.content)

                # if text_classification['label'] == 'LABEL_1':
                #     await self.add_message_to_db_bot(message, text_category, text_classification['score'])
            except Exception as e: 
                print(e)
                print(traceback.format_exc())

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
                if message.content != Review.START_KEYWORD:
                    reply =  "That is not a supported command\n"
                    reply += "Use the `help` command to see options.\n"
                    await message.channel.send(reply)
                    return
            
                if len(self.review_queue) > 0:
                    self.current_report = self.db.get(self.User["id"] == self.review_queue[0])
                    report_user = self.usersDB.get(self.User["author_id"] == self.current_report["reporter"]["author_id"])
                    ad_user = self.usersDB.get(self.User["author_id"] == self.current_report["reported_user"]["author_id"])
                    self.current_review = Review(self, self.current_report, ad_user, report_user)
                
                else:
                    await message.channel.send("There are no reported ads in the queue")
                    return

            responses = await self.current_review.handle_message(message)

            for r in responses:
                await message.channel.send(r)

            if self.current_review.state == State.REVIEW_CANCELLED:
                self.current_review = None
            
            elif self.current_review.review_complete():
                # Bad ad w/ history
                if self.current_review.final_state == 0:
                    # Delete Post
                    await self.delete_message(self.current_report["reported_user"]["channel_id"], self.current_report["reported_user"]["message_id"])
                    # Send Them A Message Saying They Have Been Banned
                    await self.dm_user(self.current_report["reported_user"]["author_id"], "Your ad has been removed for misinformation. Visit <link to \n accurate source> to learn more. Due to your history of advertising \n misinformation, your account has been banned. Our \n moderator team will  review the situation.")
                    # Ban User
                    await self.ban_user(self.current_report["reported_user"]["author_id"])

                # Bad ad w/o histrory
                if self.current_review.final_state == 1:
                    # Delete Post
                    await self.delete_message(self.current_report["reported_user"]["channel_id"], self.current_report["reported_user"]["message_id"])
                    # Send Them A Message Saying their ad was misinformation and will be removed if they keep it up
                    await self.dm_user(self.current_report["reported_user"]["author_id"], "Your ad has been removed for misinformation. Visit <link to \n accurate source> to learn more. If this problem persists, your \n account will be banned.")
                    
                # Bad report w/ history
                if self.current_review.final_state == 2:
                    # Send Them A Message Saying They Have Been Banned from reporting
                    await self.dm_user(self.current_report["reporter"]["author_id"], "The ad that you reported is not misinformation.\nDue to your history of false reporting, you have been banned from reporting advertisements.\nOur moderator team will review the situation.\n ")
                    # Ban User Reports
                    await self.ban_user_reports(self.current_report["reporter"]["author_id"])
                    
                # Bad report w/o histrory
                if self.current_review.final_state == 3:
                    # Send Them A Message Saying the ad was not misinformation and will be removed if they keep reporting badly
                    await self.dm_user(self.current_report["reporter"]["author_id"], "The ad that you reported is not misinformation.\nIf we detect a history of false reporting in the future, you may be banned from reporting advertisements.\n")

                # Update User Database
                await self.update_user_database_review(self.current_review, self.current_report)

                # Remove Report from Queue
                report_id = self.current_report["id"]
                await self.remove_report_from_queue(report_id)

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

# class ConfirmView(discord.ui.View):
#         def __init__(self, *, timeout: float | None = 180, ):
#             super().__init__(timeout=timeout)
#             self.confirmed = None
#         @discord.ui.button(label="Yes", style=discord.ButtonStyle.primary)
#         async def yes(self, interaction: discord.Interaction, button: discord.ui.Button, custom_id="yes"):
#             self.confirmed = True
#             self.clean_up()
#             await interaction.response.edit_message(view=self)
#             await interaction.followup.send("You confirmed!")

#         @discord.ui.button(label="No", style=discord.ButtonStyle.secondary, custom_id="no")
#         async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
#             self.confirmed = False
#             self.clean_up()
#             await interaction.response.edit_message(view=self)
#             await interaction.followup.send("You did not confirm. Please try again.")
        
#         def clean_up(self):
#             for x in self.children:
#                 x.disabled = True
#             # button.disabled = True
#             self.stop()


client = ModBot()
client.run(discord_token)


