
''' 
TODO: 
get the list of user-chats by calling /api/userchats
loop over 'userChats', checking the 'managerIds' of each chat with the id we are checking
    if the id is in the 'managerIds', get the chat messages from the 'userChats' by calling the '/api/userchats/<chatId>/messages' endpoint
    else, skip

'''



from flask import Flask, redirect, render_template, request, flash, jsonify, send_file
from dotenv import load_dotenv
import os
import requests
from collections import defaultdict

app = Flask(__name__)

load_dotenv()

# app.config["ACCESS_KEY"] = os.getenv("ACCESS_KEY")
# app.config["ACCESS_SECRET"] = os.getenv("ACCESS_SECRET")

# ACCESS_KEY = app.config["ACCESS_KEY"]
# ACCESS_SECRET = app.config["ACCESS_SECRET"]

ACCESS_KEY = os.getenv("ACCESS_KEY")
ACCESS_SECRET = os.getenv("ACCESS_SECRET")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/<endpoint>", methods=["GET"])
def get(endpoint: str) -> dict:
    '''
    examples: 
        endpoint = 'users'
        endpoint = 'managers'
        endpoint = 'managers/<manager_id>'
    '''
    headers = {
        "Content-Type": "application/json",
        "X-Access-Key": ACCESS_KEY,
        "X-Access-Secret": ACCESS_SECRET,
    }
    print("http://api.channel.io/open/v5" + endpoint)
    response = requests.get("http://api.channel.io/open/v5/" + endpoint, headers=headers, json=True)
    return response.json()






@app.route("/api/userchats", methods=["GET"])
def get_chats() -> dict:
    headers = {
        "Content-Type": "application/json",
        "X-Access-Key": ACCESS_KEY,
        "X-Access-Secret": ACCESS_SECRET,
    }
    response = requests.get("http://api.channel.io/open/v5/user-chats?sortOrder=desc&limit=30", headers=headers, json=True)
    return response.json()


@app.route("/api/userchats/<chatId>", methods=["GET"])
def get_chat_messages(chatId: str) -> dict:
    headers = {
        "Content-Type": "application/json",
        "X-Access-Key": ACCESS_KEY,
        "X-Access-Secret": ACCESS_SECRET,
    }
    response = requests.get("http://api.channel.io/open/v5/user-chats/" + chatId + "/messages?sortOrder=desc&limit=25", headers=headers, json=True)
    response.encoding = "utf-8"
    return response.json()

@app.route("/api/sessions/<chatId>", methods=["GET"])
def get_chat_sessions(chatId: str) -> dict:
    headers = {
        "Content-Type": "application/json",
        "X-Access-Key": ACCESS_KEY,
        "X-Access-Secret": ACCESS_SECRET,
    }
    response = requests.get("http://api.channel.io/open/v5/user-chats/" + chatId + "/sessions", headers=headers, json=True)
    response.encoding = "utf-8"
    return response.json()


# 339530
@app.route("/api/check/<managerId>")
def check_if_manager_exists_in_userchats(managerId):
    result = list()
    _ids = list()
    _userChats = get_chats()["userChats"]
    for userChat in _userChats:
        if managerId in userChat["managerIds"]:
            # print(userChat["name"], userChat["id"])
            _ids.append(userChat["id"])

    for id in _ids:
        _messages = get_chat_messages(id)["messages"]
        for message in _messages:
            if "blocks" in message and isinstance(message["blocks"], list):
                for block in message["blocks"]:
                    if "type" in block and block["type"] == "text" and "value" in block:
                        result.append(block["value"])




    return result


if __name__ == "__main__":
    app.debug = True
    app.run(host='localhost', port=5010)

