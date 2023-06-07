from enum import Enum, auto
import discord
import re
from tinydb import TinyDB, Query
import random

class AD_STATE(Enum):
    AD_START = auto() #1
    AD_CANCELLED = auto()
    AD_OBJECTIVE_SELECTED = auto()
    AUDIENCE_IDENTIFIED = auto()
    AD_TITLE_CONFIGURED = auto()
    AD_PENDING_REVIEW = auto()
    # AWAITING_MESSAGE = auto() # 2
    # MESSAGE_IDENTIFIED = auto() # 3
    # MESSAGE_CONFIRMED = auto() # 4
    # MISINFORMATION_REPORT = auto()
    # SPAM_REPORT = auto()
    # OFF_CON_REPORT = auto()
    # HARASS_REPORT = auto()
    # IMM_DANG_REPORT = auto()
    # REPORT_COMPLETE = auto()
    # REPORT_CANCELLED = auto()
    # AWAITING_BLOCK_USER = auto()
    # REVIEW_START = auto()
    # AWAITING_MISINFO = auto()
    # EVENT_CLASSIFICATION = auto()
    # EVENT_FIX = auto()
    # HISTORY_AD = auto()
    # HISTORY_REPORT = auto()
    # REVIEW_COMPLETE = auto()
    # REVIEW_CANCELLED = auto()
    # AWAITING_MISINFO_CLARITY = auto()
    # AWAITING_MISINFO_CLARITY_OTHER_REASON = auto()

class Ad:
    #class variable
    CREATE_AD = 'Create an ad'
    CANCEL_KEYWORD = "cancel"
    OBJECTIVE_OPTIONS = ["awareness", "traffic", "engagement", "leads", "app promotion", "sales"]
    AUDIENCE_OPTIONS = ["18-24 year olds", "24-45 year olds", "45+ years old", "highly engaged users", "san francisco residents", "east bay residents", "north bay residents", "south bay residents", "peninsula residents","outer bay residents"]
    
    def __init__(self, client):
        self.state = AD_STATE.AD_START
        # self.num_state = 0 #0 = start 
        self.client = client
        self.message = None
        self.ad_objective = ""
        self.ad_audience_selections = []
        self.ad_title = ""
        self.ad_content = ""
        self.advertiser = {"author_id": None, "author_name": None, "ad_id": None, "channel_id": None}
        self.current_ad = {"id": None, "objective": None, "audience" : None, "title": None, "content": None}
        print("THIS IS CLIENT", client, client.user)
        # self.report_reason = ""
        # self.report_clarity_reason = ""
        # self.handle_reported_user = ""
        # prev_reports = []

        self.advertiser = {"author_id": None, "author_name": None, "message_id": None, "channel_id": None}
    
    async def fill_out_advertiser_info(self, advertiser):
        print(advertiser)
        self.advertiser = {"author_id": advertiser["author_id"],
                           "author_name": advertiser["author_name"],
                           "ad_id": advertiser["ad_id"],
                           "channel_id": advertiser["author_id"]}
        self.current_ad["id"] = advertiser["ad_id"]
        total_ad_info = {"advertiser": self.advertiser, "ad": self.current_ad}
        return total_ad_info
               
    async def handle_message(self, message):
        '''
        This function makes up the meat of the user-side reporting flow. It defines how we transition between states and what 
        prompts to offer at each of those states. You're welcome to change anything you want; this skeleton is just here to
        get you started and give you a model for working with Discord. 
        '''
        if not isinstance(message, str):
            if not isinstance(message, list):
            #message is not message object from discord
                if message.content == self.CANCEL_KEYWORD:
                    self.state = AD_STATE.AD_CANCELLED
                    return ["Advertisement cancelled."]
        print("THIS IS MESSAGE = ", message)

        if self.state == AD_STATE.AD_START:
            user_msg = message
            user_msg = user_msg.lower()
            if user_msg in self.OBJECTIVE_OPTIONS:
                self.state = AD_STATE.AD_OBJECTIVE_SELECTED
                self.ad_objective = user_msg
                self.current_ad["objective"] = user_msg
                reply = "Great! Now that you selected `" + user_msg + "` as an objective, let's define your audience. \n"
                reply += "Select your preferred audiences from the select menu.\n"
                reply += "If you would like to cancel at anytime, type `cancel` to exit."
                return [reply]
            else:
                reply = "Sorry, there seems to be a problem.\n"
                reply += "Please re-try creating an advertisement!\n"
                reply += "Goodbye."
                self.state = AD_STATE.AD_CANCELLED
                return [reply]

        if self.state == AD_STATE.AD_OBJECTIVE_SELECTED:
            user_selections = [selection.lower() for selection in message]
            if set(user_selections).issubset(set(Ad.AUDIENCE_OPTIONS)):
                self.ad_audience_selections = user_selections
                selections = ", ".join(user_selections)
                self.current_ad["audience"] = user_selections
                self.state = AD_STATE.AUDIENCE_IDENTIFIED
                reply = "Great! Now that you selected your audiences: `" + selections + "`, let's get your advertising material. \n\n"
                reply += "Type in the title of the ad you want to create.\n"
                reply += "If you would like to cancel at anytime, type `cancel` to exit."
                return [reply]
            else:
                reply = "Sorry, there seems to be a problem.\n"
                reply += "Please re-try creating an advertisement!\n"
                reply += "Goodbye."
                self.state = AD_STATE.AD_CANCELLED
                return [reply]
            
        if self.state == AD_STATE.AUDIENCE_IDENTIFIED:
            user_msg = message
            if user_msg is not None or len(user_msg) != 0:
                self.ad_title = user_msg
                self.state = AD_STATE.AD_TITLE_CONFIGURED
                self.current_ad["title"] = user_msg
                reply = "Great! Now that you set your ad title: `" + user_msg + "`, let's write the content for your ad. \n\n"
                reply += "Type in the description or content you want to promote. \n"
                reply += "If you would like to cancel at anytime, type `cancel` to exit."
                return [reply]
            else:
                reply = "Sorry, there seems to be a problem.\n"
                reply += "Please re-try creating an advertisement!\n"
                reply += "Goodbye."
                self.state = AD_STATE.AD_CANCELLED
                return [reply]
            
        if self.state == AD_STATE.AD_TITLE_CONFIGURED:
            user_msg = message
            if user_msg is not None or len(user_msg) != 0:
                self.ad_content = user_msg
                self.state = AD_STATE.AD_PENDING_REVIEW
                self.current_ad["content"] = user_msg
                reply = "Great! Now that you've written your ad content: `" + user_msg + "`, you're done!. \n\n"
                reply += "Below is what your advertisement looks like! \n\n"
                return [reply], self.current_ad
            else:
                reply = "Sorry, there seems to be a problem.\n"
                reply += "Please re-try creating an advertisement!\n"
                reply += "Goodbye."
                self.state = AD_STATE.AD_CANCELLED
                return [reply], self.current_ad

    
        return []

    def format_message(self, message):
        user_msg = message.content
        user_msg = user_msg.lower()
        return user_msg
    
    def save_report(self):
        db = TinyDB('db.json')

    def report_complete(self):
        db = TinyDB('db.json')
        id = random.randint(0, 1200) 
        reported_user = self.reported_user_info
        report = {"report_type": self.report_type, "report_reason": self.report_reason, "report_clarity_reason": self.report_clarity_reason, "report_resolution": self.handle_reported_user}
        reporter = self.reporter
        db.insert({"id": id, "reporter" : reporter, "reported_user": reported_user, "report": report})
        print("saved to db successfully")

        return id

    def report_cancelled(self):
        return self.state == AD_STATE.AD_CANCELLED
    


    
