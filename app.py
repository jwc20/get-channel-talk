from flask import Flask, redirect, render_template, request, flash, jsonify, send_file
from dotenv import load_dotenv
import os
import requests
from typing import DefaultDict, List, Dict
from collections import defaultdict, deque
from datetime import datetime
import base64
import urllib.parse

from pprintpp import pprint

app = Flask(__name__)

load_dotenv()
ACCESS_KEY = os.getenv("ACCESS_KEY")
ACCESS_SECRET = os.getenv("ACCESS_SECRET")

# ---Helper Functions-----------------------------------


def convert_timestamp_to_date(timestamp: int) -> str:
    """
    input: timestamp in milliseconds
    output: date in the format 'Year-Month-Day Hour:Minute:Second'
    """
    date_time = datetime.utcfromtimestamp(timestamp / 1000)
    return date_time.strftime("%Y-%m-%d %H:%M:%S")


# ------------------------------------------------------
# ---Routes---------------------------------------------


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/<endpoint>", methods=["GET"])
def get(endpoint: str) -> dict:
    """
    examples:
        endpoint = 'users'
        endpoint = 'managers'
        endpoint = 'managers/<manager_id>'
    """
    headers = {
        "Content-Type": "application/json",
        "X-Access-Key": ACCESS_KEY,
        "X-Access-Secret": ACCESS_SECRET,
    }
    print("http://api.channel.io/open/v5" + endpoint)
    response = requests.get(
        "http://api.channel.io/open/v5/" + endpoint, headers=headers, json=True
    )
    return response.json()


# TODO: Add pagination
@app.route("/api/messages/<chatId>", methods=["GET"])
def get_chat_messages(chatId: str) -> dict:
    headers = {
        "Content-Type": "application/json",
        "X-Access-Key": ACCESS_KEY,
        "X-Access-Secret": ACCESS_SECRET,
    }
    response = requests.get(
        "http://api.channel.io/open/v5/user-chats/"
        + chatId
        + "/messages?sortOrder=asc&limit=25",
        headers=headers,
        json=True,
    )
    response.encoding = "utf-8"
    return response.json()

# @app.route("/api/sessions/<chatId>", methods=["GET"])
# def get_chat_sessions(chatId: str) -> dict:
#     headers = {
#         "Content-Type": "application/json",
#         "X-Access-Key": ACCESS_KEY,
#         "X-Access-Secret": ACCESS_SECRET,
#     }
#     response = requests.get(
#         "http://api.channel.io/open/v5/user-chats/" + chatId + "/sessions",
#         headers=headers,
#         json=True,
#     )
#     response.encoding = "utf-8"
#     return response.json()

# @app.route("/api/userchats", methods=["GET"])
def get_chats(
    state: str = "opened", sort_order: str = "desc", limit: str = "25", arr: DefaultDict = defaultdict(list)
) -> dict:

    # TODO add list of users, add list of managers in the userchats

    headers = {
        "Content-Type": "application/json",
        "X-Access-Key": ACCESS_KEY,
        "X-Access-Secret": ACCESS_SECRET,
    }
    
    state = state.lower() if state != "all" else state
    sort_order = sort_order.lower() if sort_order in ["asc", "desc"] else "desc"
    _limit = int(limit)

    url = f"http://api.channel.io/open/v5/user-chats?state={state}" \
          f"&sortOrder={sort_order}&limit={limit}"
    
    while _limit > 0:
        response = requests.get(url, headers=headers, json=True)
        # arr[state].extend(response.json()["userChats"])
        _limit -= 25
        if response.status_code == 200:
            arr[state].extend(response.json()["userChats"])
            if "next" in response.json():
                next_string = urllib.parse.quote(response.json()["next"], safe='')
                url += "&since=" + next_string
                
                print(arr[state], _limit)
                # print(response.json()["next"])
                print(len(response.json()["userChats"]))
            else:
                break
        else:
            break
    
    # response = requests.get(url, headers=headers, json=True)
    # if response.status_code == 200:
    #     if "next" in response.json():
    #         print(response.json()["next"])
    #         print(len(response.json()["userChats"]))
    #     arr[state].extend(response.json()["userChats"])

    # {k: [*map(pprint, v[:3])] for k, v in arr.items()}
    # print(arr)
    return arr

@app.route("/api/managers/<manager_id>/chats", methods=["GET"])
@app.route("/api/managers/<manager_id>/chats/<state>", methods=["GET"])
@app.route("/api/managers/<manager_id>/chats/<state>/<limit>", methods=["GET"])
@app.route("/api/managers/<manager_id>/chats/<state>/<limit>/<sort_order>", methods=["GET"])
def check_if_manager_exists_in_userchats(manager_id: str, state: str="all", limit: str="25", sort_order: str="desc") -> List[dict]:
    result = []
    _ids = []
    _arr = defaultdict(list)
    states = "all opened closed snoozed".split()
    sorts = "asc desc".split()
    
    # print(limit)

    state = state if state in states else ""
    sort_order = sort_order if sort_order in sorts else ""
    # limit = min(max(int(limit), 500), 25)

    if state == "all":
        for s in ["opened", "closed", "snoozed"]:
            _userChats = get_chats(state=s, limit=limit, sort_order=sort_order, arr=_arr)
            for userChat in _userChats[s]:
                if "managerIds" not in userChat:
                    continue

                if manager_id in userChat["managerIds"]:
                    _ids.append(userChat["id"])
    
    else:
        _userChats = get_chats(state=state, limit=limit, sort_order=sort_order, arr=_arr)
        for userChat in _userChats[state]:
            if "managerIds" not in userChat:
                continue

            if manager_id in userChat["managerIds"]:
                _ids.append(userChat["id"])

    # print(_ids)
    for id in _ids:
        print(id)
        _messages = get_chat_messages(id)["messages"]

        
        
        for message in _messages:
            if _userChats["id"] == id and message["personType"] == "user" and _userChats["userId"] == message["id"]:
                inquirer = _userChats["name"]

            if message["personType"] == "bot":
                continue
                

            if "plainText" in message:
                result.append(f"{message['personType']}  {message['plainText']}")
            
            # if "blocks" in message and isinstance(message["blocks"], list):
            #     for block in message["blocks"]:
            #         if "type" in block and block["type"] == "text" and "value" in block:
            #             result.append(block["value"])
                        # result.append(message)
                        # print(convert_timestamp_to_date(message["createdAt"]), block["value"])

    return result


# ------------------------------------------------------


if __name__ == "__main__":
    app.debug = True
    app.run(host="localhost", port=5010)
