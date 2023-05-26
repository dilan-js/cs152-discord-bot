from enum import Enum, auto
import discord
import re
from report import State

class Review:
    #class variable
    START_KEYWORD = "review"
    CANCEL_KEYWORD = "cancel"
    HELP_KEYWORD = "help"
    

    def __init__(self, client, ad, advertiser_info, reporter_info):
        self.state = State.REVIEW_START
        # self.num_state = 0 #0 = start 
        self.client = client
        self.ad = ad
        self.info = {'advertiser': advertiser_info, 'reporter': reporter_info}
        self.final_state = None

    
    async def handle_message(self, message):
        ''' 
        This function makes up the meat of the user-side reporting flow. It defines how we transition between states and what 
        prompts to offer at each of those states. You're welcome to change anything you want; this skeleton is just here to
        get you started and give you a model for working with Discord. 
        '''

        if message.content == self.CANCEL_KEYWORD:
            self.state = State.REVIEW_CANCELLED
            return ["Review cancelled, this post will remian at the top of the review queue."]
        
        if self.state == State.REVIEW_START:
            reply =  "Thank you for starting the review process. "
            reply += "Say `help` at any time for more information.\n\n"
            reply += "Information on the Reported Ad:\n"
            reply += "Ad - Message ID: " + str(self.ad[1].PERP_INFO["message_id"]) + " \n"
            reply += "Advertiser - Total Reports: " + str(self.info['advertiser']['reported']) + " - False Ads: "+ str(self.info['advertiser']['false']) +" \n"
            reply += "Reporter - Total Reports: " + str(self.info['reporter']['reported']) + " - False Reports: "+ str(self.info['reporter']['false']) +" \n\n"
            self.state = State.AWAITING_MISINFO
            return [reply, "Does this violate our policy on misinformation? Type `yes` or `no` based on your assessment"]
        
        if self.state == State.AWAITING_MISINFO:
            user_msg = message.content
            user_msg = user_msg.lower()

            if user_msg == 'yes':
                self.state = State.EVENT_CLASSIFICATION
                return ["Is the ad event correctly classified? Type `yes` or `no` based on your assessment"]
            elif user_msg == 'no':
                self.state = State.HISTORY_REPORT
                return ["Does the reporting user have a history of false reports? Type `yes` or `no` based on your assessment"]
            else:
                return ["Sorry! It looks like that was an invalid input.", "Please type `yes` or `no` based on your assessment"]
        
        if self.state == State.EVENT_CLASSIFICATION:
            user_msg = message.content
            user_msg = user_msg.lower()

            if user_msg == 'yes':
                self.state = State.HISTORY_AD
                return ["Does the advertiser have a history of ads with misinformation? Type `yes` or `no` based on your assessment"]
            elif user_msg == 'no':
                self.state = State.EVENT_FIX
                return ["Please enter the correct event classification", "Type: `Elections`, `Major Event A`, `Major Event B` "]
            else:
                return ["Sorry! It looks like that was an invalid input.", "Please type `yes` or `no` based on your assessment"]
            
        if self.state == State.EVENT_FIX:
            user_msg = message.content
            user_msg = user_msg.lower()

            if user_msg in ['elections', 'major event a', 'major event b']:
                self.state = State.HISTORY_AD
                return ["Does the advertiser have a history of ads with misinformation? Type `yes` or `no` based on your assessment"]
            else:
                return ["Sorry! It looks like that was an invalid input.", "Please enter the correct event classification", "Type: `Elections`, `Major Event A`, `Major Event B` "]
            
        if self.state == State.HISTORY_AD:
            user_msg = message.content
            user_msg = user_msg.lower()

            if user_msg == 'yes':
                self.state = State.REVIEW_COMPLETE
                self.final_state = 1
                return ["Thank you for completing the review of this ad \n This ad will be removed and the advertiser has been temporarily banned \n This case will be elevated for evaluation for consideration of a permanent ban of the advertiser"]
            elif user_msg == 'no':
                self.state = State.REVIEW_COMPLETE
                self.final_state = 1
                return ["Thank you for completing the review of this ad \n This ad will be removed and the advertiser will be issued a warning "]
            else:
                return ["Sorry! It looks like that was an invalid input.", "Please type `yes` or `no` based on your assessment"]
            
        if self.state == State.HISTORY_AD:
            user_msg = message.content
            user_msg = user_msg.lower()

            if user_msg == 'yes':
                self.state = State.REVIEW_COMPLETE
                self.final_state = 2
                return ["Thank you for completing the review of this ad \n This reporting user has been temporarily banned from reporting ads \n This case will be elevated for evaluation for consideration of a permanent reporting ban of the user"]
            elif user_msg == 'no':
                self.state = State.REVIEW_COMPLETE
                self.final_state = 3
                return ["Thank you for completing the review of this ad \n No further action will be taken "]
            else:
                return ["Sorry! It looks like that was an invalid input.", "Please type `yes` or `no` based on your assessment"]

    def report_complete(self):
        return self.state == State.REPORT_COMPLETE
    


    
