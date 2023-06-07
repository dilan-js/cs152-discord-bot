import openai
import json
import os
import pickle
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC


class Automation:
    MODEL = "jy46604790/Fake-News-Bert-Detect"
    LABELS = ["Elections", "COVID", "News", "Other", "Russia"]
    AUTOMATIC_APPROVAL = 0.27
    AUTOMATIC_REJECTION = 0.6

    def __init__(self): 
        # Load the vectorizer from the file
        with open('vectorizer.pkl', 'rb') as f:
            self.vectorizer = pickle.load(f)

        # Load the classifier from the file
        with open('classifier.pkl', 'rb') as f:
            self.classifier = pickle.load(f)

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

    def classify(self, pending_ad=None, is_Ad=True):
        text_input = str(pending_ad['ad']['title']) + " " + str(pending_ad['ad']['content'])
        input_vector = self.vectorizer.transform([text_input])
        prediction = self.classifier.decision_function(input_vector)
        return prediction[0]
    
    def categorize(self, classified_ad=None, is_Ad=True):
        text_input = str(classified_ad['ad']['title']) + " " + str(classified_ad['ad']['content'])
        prompt_text = self.prompt_template + text_input
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