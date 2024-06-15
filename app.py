from flask import Flask, redirect, render_template, request, flash, jsonify, send_file
from dotenv import load_dotenv
import os
import requests
from typing import DefaultDict, List, Dict
from collections import defaultdict, deque
from datetime import datetime, timezone
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
    date_time =  datetime.fromtimestamp(timestamp / 1000, timezone.utc)
    return date_time.strftime("%Y-%m-%d %H:%M:%S")

def convert_timestamp_to_date_without_time(timestamp: int) -> str:
    """
    input: timestamp in milliseconds
    output: date in the format 'Year-Month-Day'
    """
    date_time =  datetime.fromtimestamp(timestamp / 1000, timezone.utc)
    return date_time.strftime("%Y-%m-%d")
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
    state: str = "opened",
    sort_order: str = "desc",
    limit: str = "25",
    arr: DefaultDict = defaultdict(list),
) -> dict:

    headers = {
        "Content-Type": "application/json",
        "X-Access-Key": ACCESS_KEY,
        "X-Access-Secret": ACCESS_SECRET,
    }

    state = state.lower() if state != "all" else state
    sort_order = sort_order.lower() if sort_order in ["asc", "desc"] else "desc"
    _limit = int(limit)

    url = (
        f"http://api.channel.io/open/v5/user-chats?state={state}"
        f"&sortOrder={sort_order}&limit={limit}"
    )

    while _limit > 0:
        response = requests.get(url, headers=headers, json=True)

        # TODO add list of users, add list of managers in the userchats
        participants = []

        userChats = response.json()["userChats"]

        if "managers" in response.json():
            managers = response.json()["managers"]

        for userChat in userChats:
            participants.append(
                {"id": userChat["userId"], "name": userChat["name"], "type": "user"}
            )

            if "managerIds" in userChat:
                for managerId in userChat["managerIds"]:
                    manager = next((m for m in managers if m["id"] == managerId), None)
                    if manager:
                        participants.append(
                            {
                                "id": managerId,
                                "name": manager["name"],
                                "type": "manager",
                            }
                        )
                        # print({"id": managerId, "name": manager["name"], "type": "manager"})

        for participant in participants:
            if not any(d["id"] == participant["id"] for d in arr["participants"]):
                arr["participants"].append(participant)

        arr[state].extend(userChats)

        # print(arr["participants"])

        # arr[state].extend(response.json()["userChats"])
        _limit -= 25
        if response.status_code == 200:

            if "next" in response.json():
                next_string = urllib.parse.quote(response.json()["next"], safe="")
                url += "&since=" + next_string

                # print(arr[state], _limit)
                # print(response.json()["next"])
                # print(len(response.json()["userChats"]))
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
@app.route(
    "/api/managers/<manager_id>/chats/<state>/<limit>/<sort_order>", methods=["GET"]
)
@app.route(
    "/api/managers/<manager_id>/chats/<state>/<limit>/<sort_order>/<date>", methods=["GET"]
)
def get_chats_by_manager_id(
    manager_id: str, state: str = "all", limit: str = "25", sort_order: str = "desc", date: str = None
) -> List[dict]:
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
            _userChats = get_chats(
                state=s, limit=limit, sort_order=sort_order, arr=_arr
            )
            for userChat in _userChats[s]:
                if "managerIds" not in userChat:
                    continue

                if manager_id in userChat["managerIds"]:
                    _ids.append(userChat["id"])

    else:
        _userChats = get_chats(
            state=state, limit=limit, sort_order=sort_order, arr=_arr
        )
        for userChat in _userChats[state]:
            if "managerIds" not in userChat:
                continue

            if manager_id in userChat["managerIds"]:
                _ids.append(userChat["id"])

    for id in _ids:
        chat_messages = []
        _messages = get_chat_messages(id)["messages"]

        for message in _messages:
            message_created_at = convert_timestamp_to_date_without_time(message["createdAt"])
            
            if date is not None and message_created_at != date:
                break
                

            if message["personType"] == "bot":
                continue
            for participant in _userChats["participants"]:
                if message["personId"] == participant["id"]:
                    if "plainText" in message:
                        # chat_messages.append(
                        #     f"{convert_timestamp_to_date(message['createdAt'])} |  {participant['name']} |  {message['plainText']}"
                        # )
                        chat_messages.append(
                            {
                                "created_at": convert_timestamp_to_date(message["createdAt"]),
                                "participant_name": participant["name"],
                                "chat_message": message["plainText"],
                            }
                        )

        if len(chat_messages) == 0:
            continue

        created_at = chat_messages[0]["created_at"]
        last_message_date = chat_messages[-1]["created_at"]

        result.append(
            {
                "chat_id": id,
                "created_at": str(created_at),
                "last_message_date": str(last_message_date),
                "messages": chat_messages,
            }
        )


    return result


# ------------------------------------------------------


if __name__ == "__main__":
    app.debug = True
    app.run(host="localhost", port=5010)
