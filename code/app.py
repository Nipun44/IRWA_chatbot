from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import json
from chatbot import chatbot_response
from flask_cors import CORS
with open('code/intents2.json') as json_file:
    intents_json = json.load(json_file)

app = Flask(__name__)
CORS(app)


@app.get("/")
def index_get():
    return render_template("base.html")

@app.route('/predict', methods=['POST'])
def predict():

    data = request.get_json()
    text = data.get('message', '')
    
    text = request.get_json("message")
    # TODO: check if text is valid
    res = chatbot_response(text)
    message = {"answer": res}
    return jsonify(message)

if __name__ == "__main__":
    app.run(debug = True)