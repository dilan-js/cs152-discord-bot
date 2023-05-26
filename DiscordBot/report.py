from enum import Enum, auto
import discord
import re

class State(Enum):
    REPORT_START = auto() #1
    AWAITING_MESSAGE = auto() # 2
    MESSAGE_IDENTIFIED = auto() # 3
    MESSAGE_CONFIRMED = auto() # 4
    MISINFORMATION_REPORT = auto()
    SPAM_REPORT = auto()
    OFF_CON_REPORT = auto()
    HARASS_REPORT = auto()
    IMM_DANG_REPORT = auto()
    REPORT_COMPLETE = auto()
    REPORT_CANCELLED = auto()
    AWAITING_BLOCK_USER = auto()
    AWAITING_MISINFO_CLARITY = auto()
    AWAITING_MISINFO_CLARITY_OTHER_REASON = auto()

class Report:
    #class variable
    START_KEYWORD = "report"
    CANCEL_KEYWORD = "cancel"
    HELP_KEYWORD = "help"
    MESSAGE_CONFIRMED = "yes"
    MISINFORMATION_REASON = ['misinformation/disinformation', 'misinformation', 'disinformation', 'mis-disinformation']
    SPAM_REASON = "spam"
    OFF_CON_REASON = "offensive content"
    HARASS_REASON = "harassment"
    IMM_DANG_REASON = "imminent danger"
    MISINFORMATION_REASONS = ["manipulated content", "impersonation of other sources", "reporting error", "scam", "untrue/false", "satire/parody", "propaganda"]
    SPAM_REASONS = ["fraud/scam", "solicitation", "impersonation"]
    OFF_CON_REASONS = ["hate speech", "sexually explicit content", "child sexual abuse material", "advocating or glorifying violence", "copyright infringement"]
    HARASS_REASONS = ["bullying", "hate speech directed at me", "unwanted sexual content", "revealing private information"]
    IMM_DANG_REASONS = ["self harm or suicidal intent", "credible threat of violence"]
    MISINFO_CLARITY_REASON_ELECTION = ["ron desantis", "presidential campaign", "ron desantis", "ron", "desantis"]
    MISINFO_CLARITY_REASON_DONALD = ["donald trump trials", "donald trump", "donald", "trump"]
    MISINFO_CLARITY_REASON_RUSSIA = ["conflict between russia and ukraine", "russia", "ukraine", "russia ukraine"]
    MISINFO_CLARITY_REASON_COVID = ["covid or vaccination", "covid", "vaccinations", "covid-19", "vax"]
    MISINFO_CLARITY_REASONS = [["ron desantis", "presidential campaign", "ron desantis", "ron", "desantis"], 
        ["donald trump trials", "donald trump", "donald", "trump"], 
        ["conflict between russia and ukraine", "russia", "ukraine", "russia ukraine"],
        ["covid or vaccination", "covid", "vaccinations", "covid-19", "vax"], 
        ["no"]]
    BLOCK_USER = "yes"
    DO_NOT_BLOCK_USER = "no"
    BLOCK_ADVERTISER = ["block advertiser", "block"]
    DO_NOTHING = ["nothing", "do nothing"]
    

    def __init__(self, client):
        self.state = State.REPORT_START
        # self.num_state = 0 #0 = start 
        self.client = client
        self.message = None
        self.PERP_INFO = {"message_id": None, "channel_id": None, "author_id": None, "author_name": None}
        self.report_reason = None
        self.report_clarity_reason = None
    
    async def handle_message(self, message):
        '''
        This function makes up the meat of the user-side reporting flow. It defines how we transition between states and what 
        prompts to offer at each of those states. You're welcome to change anything you want; this skeleton is just here to
        get you started and give you a model for working with Discord. 
        '''

        if message.content == self.CANCEL_KEYWORD:
            self.state = State.REPORT_CANCELLED
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
            print("This is m = ", m)
            
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
                print(message)
                print(message.id)
                print(message.author.id)
                print(message.author.name)
                print(message.channel.id)
            except discord.errors.NotFound:
                return ["It seems this message was deleted or never existed. Please try again or say `cancel` to cancel."]

            # Here we've found the message - it's up to you to decide what to do next!
            self.state = State.MESSAGE_IDENTIFIED
            print("THIS IS MESSAGE BEFORE = ", message.content)
            message.content = message.content.lower().strip()
            print("THIS IS MESSAGE AFTER = ", message.content)
            self.PERP_INFO["message_id"] = message.id
            self.PERP_INFO["channel_id"] = message.channel.id
            self.PERP_INFO["author_id"] = message.author.id
            self.PERP_INFO["author_name"] = message.author.name

            print('perp info = ', self.PERP_INFO)
            return ["I found this message:", "```" + message.author.name + ": " + message.content + "```", \
                    "Is this the correct message? Type 'yes' to continue or type 'cancel' to restart."]
        
        if self.state == State.MESSAGE_IDENTIFIED:
            #handle here for words that we do not expect, set self.state = State.REPORT_COMPLETE return ["Report cancelled."]
            if message.content == 'yes':
                self.state = State.MESSAGE_CONFIRMED
                return ["Please type the reason for reporting this message from the following list:", \
                        "• Misinformation/Disinformation", \
                        "• Offensive Content", \
                        "• Harassment", \
                        "• Imminent Danger", \
                        "• Promotes Terrorism", \
                        "• Spam", \
                        "• Other"]
            #else try again?
            else:
                return ["Sorry! It looks like that was an invalid input.", \
                        "Please type the reason for reporting this message from the following list:", \
                        "• Misinformation/Disinformation", \
                        "• Offensive Content", \
                        "• Harassment", \
                        "• Imminent Danger", \
                        "• Promotes Terrorism", \
                        "• Spam", \
                        "• Other"]

        if self.state == State.MESSAGE_CONFIRMED:
            #they've confirmed and typed in a reason 
            user_msg = message.content
            user_msg = user_msg.lower()
            user_msg = user_msg.strip()
            print("THIS IS USER MSG = ", user_msg)
            reasons = [self.SPAM_REASON, self.OFF_CON_REASON, self.HARASS_REASON, self.IMM_DANG_REASON]
            if user_msg in reasons or user_msg in self.MISINFORMATION_REASON:
                print("FOUND IN LINE 145")
                if user_msg in self.MISINFORMATION_REASON:
                    print("found misinformation")
                    self.state = State.MISINFORMATION_REPORT
                    return ["Please type out the type of " + user_msg, \
                            "• Manipulated content", \
                            "• Impersonation of other sources", \
                            "• Reporting Error", \
                            "• Scam", \
                            "• Untrue/False", \
                            "• Satire/Parody", \
                            "• Propaganda"
                            ]
                
                elif user_msg == 'spam':
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
                    return ["Please select the type of " + user_msg, \
                            "Type: 'Bullying', 'Hate speech directed at me', 'Unwanted sexual content', 'Revealing private information', or type 'cancel' to restart"
                            ]
                elif user_msg == 'imminent danger':
                    self.state = State.IMM_DANG_REPORT
                    return ["Please select the type of " + user_msg, \
                            "Type: 'Self harm or suicidal intent', 'Credible threat of violence', or type 'cancel' to restart"
                            ]
            else:
                return ["Invalid input. Please type 'cancel' and try again."]
               
        if self.state == State.MISINFORMATION_REPORT:
            user_msg = message.content
            user_msg = user_msg.lower()
            user_msg = user_msg.strip()
            if user_msg in self.MISINFORMATION_REASONS:
                misinfo_reason = next((reason for reason in self.MISINFORMATION_REASONS if user_msg == reason), ["error"])
                self.report_reason = misinfo_reason
                #ADD IN DB 
                self.state = State.AWAITING_MISINFO_CLARITY
                return ["Thank you for reporting a potential instance of " + misinfo_reason + ".", \
                        "Is it related to any of the following?", \
                        "• Ron DeSantis' presidential campaign", \
                        "• Donald Trump trials", \
                        "• Conflict between Russia and Ukraine", \
                        "• COVID or vaccinations", \
                        "• No", \
                        ]
        elif self.state == State.SPAM_REPORT:
            user_msg = message.content
            user_msg = user_msg.lower()
            if user_msg in self.SPAM_REASONS:
                #add in error handling
                spam_reason = next((reason for reason in self.SPAM_REASONS if user_msg == reason), ["error"])
                self.state = State.AWAITING_BLOCK_USER
                return ["Thank you for reporting a potential instance of " + spam_reason + ". Our content moderation team will review the message(s) and decide on appropriate action. This may include post and/or account removal.", \
                        "Would you like to block this user to prevent them from sending you more messages in the future? Please type 'Yes' or 'No.'"]
        elif self.state == State.OFF_CON_REPORT:
            user_msg = message.content
            user_msg = user_msg.lower()
            if user_msg in self.OFF_CON_REASONS:
                self.state = State.AWAITING_BLOCK_USER
                off_con_reason = next((reason for reason in self.OFF_CON_REASONS if user_msg == reason), ["error"])
                return ["Thank you for reporting a potential instance of " + off_con_reason + ". Our content moderation team will review the message(s) and decide on appropriate action. This may include post and/or account removal.", \
                        "Would you like to block this user to prevent them from sending you more messages in the future? Please type 'Yes' or 'No.'"]
        elif self.state == State.HARASS_REPORT:
            user_msg = message.content
            user_msg = user_msg.lower()
            if user_msg in self.HARASS_REASONS:
                self.state = State.AWAITING_BLOCK_USER
                harass_reason = next((reason for reason in self.HARASS_REASONS if user_msg == reason), ["error"])
                return ["Thank you for reporting a potential instance of " + harass_reason + ". Our content moderation team will review the message(s) and decide on appropriate action. This may include post and/or account removal.", \
                        "Would you like to block this user to prevent them from sending you more messages in the future? Please type 'Yes' or 'No.'"
                        ]
        elif self.state == State.IMM_DANG_REPORT:
            user_msg = message.content
            user_msg = user_msg.lower()
            if user_msg in self.IMM_DANG_REASONS:
                self.state = State.REPORT_COMPLETE
                imm_dang_reason = next((reason for reason in self.IMM_DANG_REASONS if user_msg == reason), ["error"])
                return ["Thank you for reporting a potential instance of " + imm_dang_reason + ". Our content moderation team will review the message(s) and decide on appropriate action. This may include notifying local authorities if necessary.", \
                        "Have a great day!"
                        ]

        if self.state == State.AWAITING_MISINFO_CLARITY:
            user_msg = message.content
            user_msg = user_msg.lower()
            user_msg = user_msg.strip()
            for reason_section in self.MISINFO_CLARITY_REASONS:
                if user_msg in reason_section and user_msg != 'no':
                    clarity_reason = next((reason for reason in reason_section if user_msg == reason), ["error"])
                    self.report_clarity_reason = clarity_reason
                    self.state = State.AWAITING_BLOCK_USER #here we could add 'other' functionality and just retrieve user message.content and tell them to write out their 'other'
                    return ["Thank you for reporting a potential instance of misinformation/disinformation with regards to " + clarity_reason + ". Our content moderation team will review the message(s) and decide on appropriate action. This may include post and/or account removal.", \
                        "Would you like to take any of the following actions against the advertiser?" ,\
                        "• Do nothing", \
                        "• Block advertiser"
                        ] 
                elif user_msg == 'no':
                    self.state = State.AWAITING_MISINFO_CLARITY_OTHER_REASON
                    return ["It seems none of the mentioned topics fit the reason you are reporting this content. Please type out what topic this piece of misinformation is regarding or type 'No'"]
               
        if self.state == State.AWAITING_MISINFO_CLARITY_OTHER_REASON:
            user_msg = message.content
            user_msg = user_msg.lower()
            user_msg = user_msg.strip()
            if 'no' in user_msg:
                self.state = State.AWAITING_BLOCK_USER
            elif user_msg:
                self.state = State.AWAITING_BLOCK_USER
                self.report_clarity_reason = user_msg  
            return ["Thank you for reporting a potential instance of misinformation/disinformation with regards to ", \
                    "```" + user_msg + "```", \
                    "Our content moderation team will review the message(s) and decide on appropriate action. This may include post and/or account removal.", \
                    "Would you like to take any of the following actions against the advertiser?" ,\
                    "• Do nothing", \
                    "• Block advertiser"
                    ] 
          

        if self.state == State.AWAITING_BLOCK_USER:
            user_msg = message.content
            user_msg = user_msg.lower()
            if user_msg in self.BLOCK_ADVERTISER:
                self.state = State.REPORT_COMPLETE
                return ["Ok, you got it! We will block this advertiser from communicating with you.", \
                        "Have a great day!"]
            elif user_msg in self.DO_NOTHING:
                self.state = State.REPORT_COMPLETE
                return ["Ok, you got it! We will do nothing. Your report will still be reviewed!", \
                        "Have a great day!"]
            elif user_msg == self.BLOCK_USER:
                #user blocking logic in here
                self.state = State.REPORT_COMPLETE
                return ["Ok. We will block this user." , \
                        "Have a great day!"]
            elif user_msg == self.DO_NOT_BLOCK_USER:
                self.state = State.REPORT_COMPLETE
                return ["Ok. We will not block this user." , \
                        "Have a great day!"]
            else:
                return ["Oops. Try again!"]
        # if self.state == State.MESSAGE_REASON_IDENTIFIED:
        #     return 
        return []

    def format_message(self, message):
        user_msg = message.content
        user_msg = user_msg.lower()
        return user_msg

    def report_complete(self):
        return self.state == State.REPORT_COMPLETE
    

    def report_cancelled(self):
        return self.state == State.REPORT_CANCELLED
    


    
