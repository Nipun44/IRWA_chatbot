from keras.models import load_model
model = load_model('code/chatbot_model.h5')
import json
import random
import pickle
import numpy as np
import re
import nltk

from pymongo import MongoClient
from prettytable import PrettyTable


from nltk.stem import WordNetLemmatizer
lemmatizer = WordNetLemmatizer()
import json
import pickle
# from nltk.tokenize import word_tokenize
# import nltk
# nltk.download('punkt')
# nltk.download("stopwords")
# nltk.download('wordnet')


intents_json = json.loads(open('code/intents2.json').read())
words = pickle.load(open('code/words.pkl','rb'))
classes = pickle.load(open('code/classes.pkl','rb'))



# Connect to MongoDB
client = MongoClient('mongodb+srv://Nipun:irwa@cluster0.wl2trfq.mongodb.net/')
db = client['bookstore'] #db name
books_collection = db['books']
orders_collection = db['orders']
promotion_collection = db['promotions'] #table name

# Function to get the number of available books for a specific title
def get_available_books(title):
    book = books_collection.find_one({"Name": title})  # Use "Name" as the column name for book titles
    if book:
        return book['Qty']  # Use "Qty" as the column name for quantity of books
    else:
        return None  # Return None if the book is not found


def clean_up_sentence(sentence):
    print("Input to clean_up_sentence:", sentence)
    # tokenize the pattern - split words into array
    sentence_words = nltk.word_tokenize(sentence)
    print("Tokenized words:", sentence_words)
    # stem each word - create short form for word
    sentence_words = [lemmatizer.lemmatize(word.lower()) for word in sentence_words]
    print("Lemmatized words:", sentence_words)
    return sentence_words


def bow(sentence, words, show_details=True):
    # tokenize the pattern
    print("Input to bow:", sentence)
    # tokenize the pattern
    sentence_words = clean_up_sentence(sentence)
    print("Words after clean_up_sentence:", sentence_words)
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


def get_book_titles_from_db():
    # Retrieve all documents from the books_collection
    books_cursor = books_collection.find({}, {"Name": 1, "_id": 0})
    
    # Extract book titles from the cursor and return as a list
    book_titles = [book['Name'] for book in books_cursor]
    
    return book_titles

def get_order_ids_from_db():
    # Assuming you have an "Orders" collection in your database
    # Retrieve all documents from the Orders collection
    orders_cursor = orders_collection.find({}, {"Order ID": 1, "_id": 0})
    
    # Extract order IDs from the cursor and return as a list
    order_ids = [order['Order ID'] for order in orders_cursor]
    
    return order_ids


def get_order_id(raw_text):
    order_ids_from_db = get_order_ids_from_db()
    
    # Check if the extracted text matches any order ID from the database
    for order_id in order_ids_from_db:
        if str(order_id) in raw_text:
            print("get_order_id")
            print(order_id)
            return str(order_id)
    return None

def get_order_status(order_id):
    # Retrieve the status of the specified order from the database
    order = orders_collection.find_one({"Order ID": order_id})
    
    print(order)
    if order:
        return order['Status']
    else:
        return None


def get_book_title(raw_text):
    book_titles_from_db = get_book_titles_from_db()
    
    for book in book_titles_from_db:
        
        if book.lower() in raw_text.lower():
            return book
    return None


def get_book_price(book_title):
    # Retrieve the price of the specified book from the database
    book = books_collection.find_one({"Name": book_title})
    print(book)
    if book:
        return book['Price']
    else:
        return None  # Return None if the book is not found

def handle_price_query(text, intent):
    print(text)
    # Extract the book title from the user query
    book_title = get_book_title(text)
    
    
    if book_title:
        # Get the price of the specified book from the database
        book_price = get_book_price(book_title.lower())  # Ensure lowercase for consistency
        print(book_price)
        
        if book_price is not None:
            # Generate the response with the book price
            response_template = random.choice(intent['responses'])
            response = response_template.replace('{price}', str(book_price))
            response = response.replace('{book}', f"'{book_title}'")
            return response
        else:
            # If the book price is not found, provide a default response
            return f"I'm sorry, but I couldn't find the price for '{book_title}'. " \
                   "Please check back later or inquire about a different book."
    else:
        # If book title is not extracted, provide a default response
        return "I'm sorry, but I couldn't understand the book title. " \
               "Please try again with a different query."




def handle_availability_query(text, intent):
    # Extract the book title from the user query
    book_title = get_book_title(text)
    
    if book_title:
        # Get the number of available books for the specified title

                    # Get the number of available books for the specified title
                    available_books_count = get_available_books(book_title)
                    
                    if available_books_count is not None:
                        # Generate the response with the available books count
                        response_template = random.choice(intent['responses'])
                        response = response_template.replace('{count}', str(available_books_count))
                        response = response.replace('{book}', f"'{book_title}'")
                        return response
                    else:
                        # If the book is not found, provide a default response
                        return f"I'm sorry, but I couldn't find information about '{book_title}'. " \
                               "Please contact us for further assistance."
    else:
        # If book title is not extracted, provide a default response
        return "I'm sorry, but I couldn't understand the book title. " \
               "Please try again with a different query."

def get_book_description_from_db(book_title):

    # Retrieve the book description from the database based on the book title
    book = books_collection.find_one({"Name": book_title})
    print(book)
    
    if book:
        return book['Description']
    else: 
        return None 
    

def handle_order_tracking_query(text, intent):
    # Extract the order ID from the user query
    order_id = get_order_id(text)
    
    if order_id:
        # Get the status of the specified order
        order_status = get_order_status(order_id)
        
        if order_status:
            # Generate the response with the order status
            response_template = random.choice(intent['responses'])
            response = response_template.replace('{order_number}', str(order_id))
            response = response.replace('{status}', order_status)
            return response
        else:
            # If the order is not found, provide a default response
            return f"I'm sorry, but I couldn't find information about order number '{order_id}'. " \
                   "Please contact us for further assistance."
    else:
        # If order ID is not extracted, provide a default response
        return "I'm sorry, but I couldn't understand the order number. " \
               "Please try again with a different query."


def handle_description_query(raw_text, intent):
    # Extract the book title from the user query
    book_title = get_book_title(raw_text)
    
    if book_title:
        # Get the description of the specified book from the database or any other data source
        book_description = get_book_description_from_db(book_title)
        
        if book_description:
            # Generate the response with the book description
            response_template = random.choice(intent['responses'])
            response = response_template.replace('{book}', f"'{book_title}'")
            response = response.replace('{description}', f"'{book_description}'")
            return response
        else:
            # If the book description is not found, provide a default response
            return f"I'm sorry, but I couldn't find the description for '{book_title}'. " \
                   "Please contact us for further assistance."
    else:
        # If book title is not extracted, provide a default response
        return "I'm sorry, but I couldn't understand the book title. " \
               "Please try again with a different query."

def get_promotion_books():
    promotion_books = promotion_collection.find({})
    return list(promotion_books)  # Return None if the book is not found
 
   



def handle_promotion_query(intent):
    print("handle_promotion_query")
    # Retrieve promotions from your data source
    promotions = get_promotion_books()
    
    if promotions:
        # Create a PrettyTable object
        table = PrettyTable()
        table.field_names = ["Book", "Promotion (%)"]
        
        # Add data to the table
        for promotion in promotions:
            table.add_row([promotion['book'], promotion['promotion (%)']])
        
        # Choose a random response template
        response_template = random.choice(intent['responses'])
        response = response_template
        
        # Concatenate the table string to the response
        response += "\n\n" + str(table)
        
        return response
    else:
        return "I'm sorry, but there are currently no promotions available."
def getResponse(intents, intents_json, text):
    print(text)
    max_prob_intent = None
    max_prob = 0.0
    
    for intent in intents:
        # Convert the probability from string to float
        probability = float(intent['probability'])
        if probability > max_prob:
            max_prob = probability
            max_prob_intent = intent['intent']
    
    if max_prob_intent:
        print(max_prob_intent)
        list_of_intents = intents_json['intents']
        for intent in list_of_intents:
            if intent['tag'] == max_prob_intent:
                if intent['tag'] == "availability_query":
                    # Call the separate function to handle availability queries
                    return handle_availability_query(text, intent)
                elif intent['tag'] == "price_query":
                    # Call the separate function to handle price queries
                    return handle_price_query(text, intent)
                elif intent['tag'] == "description_query":
                    # Call the separate function to handle description queries
                    return handle_description_query(text, intent)
                elif intent['tag'] == "order_tracking":
                    # Call the separate function to handle order tracking queries
                    return handle_order_tracking_query(text, intent)
                elif intent['tag'] == "promotion_query":
                    return handle_promotion_query(intent)
                else:
                    return random.choice(intent['responses'])
    
    return "I'm not sure how to respond to that."


def chatbot_response(text):
    # Extract the message from the dictionary
    user_message = text.get('message', '')
    intents = predict_class(user_message, model)
    res = getResponse(intents, intents_json, user_message)
    return res


