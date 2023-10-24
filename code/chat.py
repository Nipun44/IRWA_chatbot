from keras.models import load_model
model = load_model('code/chatbot_model.h5')
import json
import random
import pickle
import numpy as np

import nltk

from pymongo import MongoClient

from nltk.stem import WordNetLemmatizer
lemmatizer = WordNetLemmatizer()
import json
import pickle
# from nltk.tokenize import word_tokenize
# import nltk
# nltk.download('punkt')
# nltk.download("stopwords")
# nltk.download('wordnet')


intents = json.loads(open('code/intents.json').read())
words = pickle.load(open('code/words.pkl','rb'))
classes = pickle.load(open('code/classes.pkl','rb'))



# Connect to MongoDB
client = MongoClient('mongodb+srv://Nipun:irwa@cluster0.wl2trfq.mongodb.net/')
db = client['bookstore'] #db name
books_collection = db['books'] #table name

# Function to get the number of available books for a specific title
def get_available_books(title):
    book = books_collection.find_one({"Name": title})  # Use "Name" as the column name for book titles
    if book:
        return book['Qty']  # Use "Qty" as the column name for quantity of books
    else:
        return None  # Return None if the book is not found


def clean_up_sentence(sentence):
    # tokenize the pattern - split words into array
    sentence_words = nltk.word_tokenize(sentence)
    # stem each word - create short form for word
    sentence_words = [lemmatizer.lemmatize(word.lower()) for word in sentence_words]
    return sentence_words
# return bag of words array: 0 or 1 for each word in the bag that exists in the sentence

def bow(sentence, words, show_details=True):
    # tokenize the pattern
    sentence_words = clean_up_sentence(sentence)
    # bag of words - matrix of N words, vocabulary matrix
    bag = [0]*len(words)
    for s in sentence_words:
        for i,w in enumerate(words):
            if w == s:
                # assign 1 if current word is in the vocabulary position
                bag[i] = 1
                if show_details:
                    print ("found in bag: %s" % w)
    return(np.array(bag))

def predict_class(sentence, model):
    # filter out predictions below a threshold
    p = bow(sentence, words,show_details=False)
    res = model.predict(np.array([p]))[0]
    ERROR_THRESHOLD = 0.25
    results = [[i,r] for i,r in enumerate(res) if r>ERROR_THRESHOLD]
    # sort by strength of probability
    results.sort(key=lambda x: x[1], reverse=True)
    return_list = []
    for r in results:
        return_list.append({"intent": classes[r[0]], "probability": str(r[1])})
    return return_list

def getResponse(ints, intents_json):
    tag = ints[0]['intent']
    list_of_intents = intents_json['intents']
    for i in list_of_intents:
        if(i['tag']== tag):
            result = random.choice(i['responses'])
            break
    return result

def chatbot_response(text):
    # Check if the user query asks for the number of available books for a specific title
    if "how many books available in" in text.lower():
        # Extract the book title from the user query (you might need more sophisticated NLP for this)
        # For simplicity, here we assume the book title is within single quotes
        title_start_index = text.find("'") + 1
        title_end_index = text.rfind("'")
        book_title = text[title_start_index:title_end_index]
        
        # Get the number of available books for the specified title
        available_books_count = get_available_books(book_title)
        
        if available_books_count is not None:
            # Generate the response with the available books count
            response = f"There are {available_books_count} available books for '{book_title}'"
        else:
            # If the book is not found, provide a default response
            response = "I'm sorry, but I couldn't find information about that book. " \
                       "Please contact us for further assistance."
        
        return response
    
    # Handle other intents and provide appropriate responses...
    
    # Default response if no specific intent is detected
    else:
        ints = predict_class(text, model)
        res = getResponse(ints, intents)
        return res
        


user_query = "How many books available in '1984'"
response = chatbot_response(user_query)
print(response)

"""GUI Interface

"""



import tkinter as tk

BG_GRAY = "#ABB2B9"
BG_COLOR = "#c5f0e3"
TEXT_COLOR = "#000000"

def send():
    msg = entry_box.get()
    entry_box.delete(0, tk.END)
    if msg.strip() != '':
        chat_log.config(state=tk.NORMAL)
        chat_log.insert(tk.END, "You: " + msg + '\n\n')
        chat_log.config(foreground="#000000", font=("Verdana", 12))

        res = chatbot_response(msg)  # Replace with your chatbot logic
        chat_log.insert(tk.END, "Bot: " + res + '\n\n')

        chat_log.config(state=tk.DISABLED)
        chat_log.yview(tk.END)

base = tk.Tk()
base.title("E-Commerce Chatbot")
base.geometry("800x600")
base.config(bg=BG_COLOR)

# Header
head_label = tk.Label(base, bg=BG_COLOR, fg=TEXT_COLOR, text="Welcome to E-Commerce Chatbot", font=("Helvetica", 20, 'bold'), pady=20)
head_label.pack(fill=tk.X)

# Chat Log
chat_log = tk.Text(base, bd=0, bg=BG_COLOR, fg=TEXT_COLOR, font=("Helvetica", 12), wrap=tk.WORD, height=10)
chat_log.config(state=tk.DISABLED)
chat_log.pack(expand=tk.YES, fill=tk.BOTH, padx=20, pady=10)

# Scrollbar for Chat Log
scrollbar = tk.Scrollbar(chat_log)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
scrollbar.config(command=chat_log.yview)
chat_log.config(yscrollcommand=scrollbar.set)

# User Input
entry_box = tk.Entry(base, bg="white", font=("Arial", 14))
entry_box.bind("<Return>", lambda event=None: send())
entry_box.pack(fill=tk.X, padx=20, pady=10, side=tk.LEFT, expand=tk.YES)

# Send Button
send_button = tk.Button(base, text="Send", command=send, font=("Verdana", 14, 'bold'), bg="#ed9061", activebackground="#3c9d9b", fg='#ffffff')
send_button.pack(padx=10, pady=10, side=tk.RIGHT)

base.mainloop()
