from transformers import pipeline
import openai
import json
import os


class Automation:
    MODEL = "jy46604790/Fake-News-Bert-Detect"
    LABELS = ["Election", "COVID", "Other"]
    AUTOMATIC_APPROVAL = 0.27
    AUTOMATIC_REJECTION = 0.6

    def __init__(self): 
        self.clf = pipeline("text-classification", model=self.MODEL, tokenizer=self.MODEL)

        # There should be a file called 'tokens.json' inside the same folder as this file
        token_path = 'tokens.json'
        tokens = None
        if not os.path.isfile(token_path):
            raise Exception(f"{token_path} not found!")
        with open(token_path) as f:
            # If you get an error here, it means your token is formatted incorrectly. Did you put it in quotes?
            tokens = json.load(f)
        openai.organization = "org-YVZe9QFuR0Ke0J0rqr7l2R2L"
        openai.api_key = tokens['openai']

        self.prompt_template = "Classify the following text as"
        for label in self.LABELS:
            self.prompt_template += " " + label + ","

    def classify(self, text=None, pending_ad=None, is_Ad=False):
       result = self.clf(text)
       #result = [{'label': 'LABEL_1', 'score': 0.9989520311355591}]
       return result[0]
    
    def categorize(self, text=None, classified_ad=None, is_Ad=False):
        prompt_text = self.prompt_template + text
        prompt = [{"role": "user", "content": prompt_text}]

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=prompt
        )
        #response = {"choices":[{"message":{"content":"Other"}}]}

        text_response = response["choices"][0]["message"]["content"]
        for label in self.LABELS:
            if label in text_response:
                return label.lower()
        else:
            return "no" 