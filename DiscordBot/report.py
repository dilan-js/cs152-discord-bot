from enum import Enum, auto
import discord
import re

class State(Enum):
    REPORT_START = auto()
    AWAITING_MESSAGE = auto()
    MESSAGE_IDENTIFIED = auto()
    MESSAGE_CONFIRMED = auto()
    SPAM_REPORT = auto()
    OFF_CON_REPORT = auto()
    HARASS_REPORT = auto()
    IMM_DANG_REPORT = auto()
    REPORT_COMPLETE = auto()

class Report:
    START_KEYWORD = "report"
    CANCEL_KEYWORD = "cancel"
    HELP_KEYWORD = "help"
    MESSAGE_CONFIRMED = "yes"
    SPAM_REASON = "spam"
    OFF_CON_REASON = "offensive content"
    HARASS_REASON = "harassment"
    IMM_DANG_REASON = "imminent danger"
    SPAM_REASONS = ["fraud/scam", "solicitation", "impersonation"]
    OFF_CON_REASONS = ["hate speech", "sexually explicit content", "child sexual abuse material", "advocating or glorifying violence", "copyright infringement"]
    HARASS_REASONS = ["bullying", "hate speech directed at me", "unwanted sexual content", "revealing private information"]
    IMM_DANG_REASONS = ["self harm or suicidal intent", "credible threat of violence"]


    def __init__(self, client):
        self.state = State.REPORT_START
        self.client = client
        self.message = None
    
    async def handle_message(self, message):
        '''
        This function makes up the meat of the user-side reporting flow. It defines how we transition between states and what 
        prompts to offer at each of those states. You're welcome to change anything you want; this skeleton is just here to
        get you started and give you a model for working with Discord. 
        '''

        if message.content == self.CANCEL_KEYWORD:
            self.state = State.REPORT_COMPLETE
            return ["Report cancelled."]
        
        if self.state == State.REPORT_START:
            reply =  "Thank you for starting the reporting process. "
            reply += "Say `help` at any time for more information.\n\n"
            reply += "Please copy paste the link to the message you want to report.\n"
            reply += "You can obtain this link by right-clicking the message and clicking `Copy Message Link`."
            self.state = State.AWAITING_MESSAGE
            return [reply]
        
        if self.state == State.AWAITING_MESSAGE:
            # Parse out the three ID strings from the message link
            m = re.search('/(\d+)/(\d+)/(\d+)', message.content)
            if not m:
                return ["I'm sorry, I couldn't read that link. Please try again or say `cancel` to cancel."]
            guild = self.client.get_guild(int(m.group(1)))
            if not guild:
                return ["I cannot accept reports of messages from guilds that I'm not in. Please have the guild owner add me to the guild and try again."]
            channel = guild.get_channel(int(m.group(2)))
            if not channel:
                return ["It seems this channel was deleted or never existed. Please try again or say `cancel` to cancel."]
            try:
                message = await channel.fetch_message(int(m.group(3)))
            except discord.errors.NotFound:
                return ["It seems this message was deleted or never existed. Please try again or say `cancel` to cancel."]

            # Here we've found the message - it's up to you to decide what to do next!
            self.state = State.MESSAGE_IDENTIFIED
            return ["I found this message:", "```" + message.author.name + ": " + message.content + "```", \
                    "Is this the correct message? Type 'yes' to continue or type 'cancel' to restart."]
        
        if self.state == State.MESSAGE_IDENTIFIED:
            #handle here for words that we do not expect, set self.state = State.REPORT_COMPLETE return ["Report cancelled."]
            if message.content == 'yes' or message.content == 'Yes' or message.content == 'YES':
                self.state = State.MESSAGE_CONFIRMED
                return ["Please type the reason for reporting this message from the following list:", \
                    "'Spam', 'Offensive Content', 'Harassment', 'Imminent Danger' or type 'cancel' to restart"]
            #else try again?
            else:
                return ["Sorry! It looks like that was an invalid input.", \
                        "Please type the reason for reporting this message from the following list:", \
                        "'Spam', 'Offensive Content', 'Harassment', 'Imminent Danger' or type 'cancel' to restart"]

        if self.state == State.MESSAGE_CONFIRMED:
            #they've confirmed and typed in a reason 
            user_msg = message.content
            user_msg = user_msg.lower()
            reasons = [self.SPAM_REASON, self.OFF_CON_REASON, self.HARASS_REASON, self.IMM_DANG_REASON]
            if user_msg in reasons:
                if user_msg == 'spam':
                    print("FOUND SPAM")
                    self.state = State.SPAM_REPORT
                    return ["Please select the type of " + user_msg]
                elif user_msg == 'offensive content':
                    self.state = State.OFF_CON_REPORT
                    return ["Please select the type of " + user_msg, \
                            "Type: 'Hate Speech', 'Sexually explicit content', 'Child sexual abuse material', 'Advocating or glorifying violence', 'Copyright infringement', or type 'cancel' to restart"
                            ]
                elif user_msg == 'harassment':
                    self.state = State.HARASS_REPORT
                    return ["Please select the type of " + user_msg]
                elif user_msg == 'imminent danger':
                    self.state = State.IMM_DANG_REPORT
                    return ["Please select the type of " + user_msg]
            else:
                return ["Oops"]
               
        if self.state == State.SPAM_REPORT:
            user_msg = message.content
            user_msg = user_msg.lower()
            if user_msg in self.SPAM_REASONS:
                #add in error handling
                spam_reason = next((reason for reason in self.SPAM_REASONS if user_msg == reason), ["error"])
                return ["Thank you for reporting a potential instance of " + spam_reason + ". Our content moderation team will review the message(s) and decide on appropriate action. This may include post and/or account removal."]
        if self.state == State.OFF_CON_REPORT:
            user_msg = message.content
            user_msg = user_msg.lower()
            if user_msg in self.OFF_CON_REASONS:
                off_con_reason = next((reason for reason in self.OFF_CON_REASONS if user_msg == reason), ["error"])
                return ["Thank you for reporting a potential instance of " + off_con_reason + ". Our content moderation team will review the message(s) and decide on appropriate action. This may include post and/or account removal."]
        if self.state == State.HARASS_REPORT:
            user_msg = message.content
            user_msg = user_msg.lower()
            if user_msg in self.HARASS_REASONS:
                harass_reason = next((reason for reason in self.HARASS_REASONS if user_msg == reason), ["error"])
                return ["Thank you for reporting a potential instance of " + harass_reason + ". Our content moderation team will review the message(s) and decide on appropriate action. This may include post and/or account removal."]
        if self.state == State.IMM_DANG_REPORT:
            user_msg = message.content
            user_msg = user_msg.lower()
            if user_msg in self.IMM_DANG_REASONS:
                imm_dang_reason = next((reason for reason in self.IMM_DANG_REASONS if user_msg == reason), ["error"])
                return ["Thank you for reporting a potential instance of " + imm_dang_reason + ". Our content moderation team will review the message(s) and decide on appropriate action. This may include post and/or account removal."]
        

        # if self.state == State.MESSAGE_REASON_IDENTIFIED:
        #     return 
        return []

    def format_message(message):
        user_msg = message.content
        user_msg = user_msg.lower()
        return user_msg

    def report_complete(self):
        return self.state == State.REPORT_COMPLETE
    


    
