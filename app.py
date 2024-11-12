from flask import Flask, redirect, render_template, request, flash, jsonify, send_file
from dotenv import load_dotenv
import os
import requests
from typing import DefaultDict, List, Dict
from collections import defaultdict, namedtuple
from datetime import datetime, timezone, timedelta
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
    date_time = datetime.fromtimestamp(timestamp / 1000, timezone(timedelta(hours=9)))
    return date_time.strftime("%Y-%m-%d %H:%M:%S")


def convert_timestamp_to_date_without_time(timestamp: int) -> str:
    """
    input: timestamp in milliseconds
    output: date in the format 'Year-Month-Day'
    """
    date_time = datetime.fromtimestamp(timestamp / 1000, timezone(timedelta(hours=9)))
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


@app.route("/api/messages/<chatId>", methods=["GET"])
def get_chat_messages(chatId: str) -> dict:
    headers = {
        "Content-Type": "application/json",
        "X-Access-Key": ACCESS_KEY,
        "X-Access-Secret": ACCESS_SECRET,
    }

    # TODO: Add pagination (?)

    response = requests.get(
        "http://api.channel.io/open/v5/user-chats/"
        + chatId
        + "/messages?sortOrder=asc&limit=100",
        headers=headers,
        json=True,
    )
    response.encoding = "utf-8"
    # pprint(response.json())
    return response.json()


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
        participants = []
        church_infos = []
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

        for participant in participants:
            if not any(d["id"] == participant["id"] for d in arr["participants"]):
                arr["participants"].append(participant)

        arr[state].extend(userChats)
        _limit -= 25
        if response.status_code == 200:

            if "next" in response.json():
                next_string = urllib.parse.quote(response.json()["next"], safe="")
                url += "&since=" + next_string
            else:
                break
        else:
            break

    # {k: [*map(pprint, v[:3])] for k, v in arr.items()}
    # pprint(arr)

    # loop over participants that are type user

    chat_users = [d for d in arr['participants'] if d['type'] == 'user']

    if 'users' in response.json():
        users = response.json()["users"]

        for u in chat_users:
            for user in users:
                church_info = {}
                if u['id'] == user['id']:
                    church_info = user['profile']
                    church_info['user_id'] = user['id'] # use this to check later
                    church_infos.append(church_info)

    arr['church_infos'] = church_infos
    # pprint(arr)
    return arr


# @app.route("/api/managers/<manager_id>/chats", methods=["GET"])
# @app.route("/api/managers/<manager_id>/chats/<state>", methods=["GET"])
# @app.route("/api/managers/<manager_id>/chats/<state>/<limit>", methods=["GET"])
# @app.route(
#     "/api/managers/<manager_id>/chats/<state>/<limit>/<sort_order>", methods=["GET"]
# )
# @app.route(
#     "/api/managers/<manager_id>/chats/<state>/<limit>/<sort_order>/<date>",
#     methods=["GET"],
# )
def get_chats_by_manager_id(
    manager_id: str,
    state: str = "all",
    limit: str = "50",
    sort_order: str = "desc",
    date: str = None,
) -> List[dict]:
    result = {}
    chats = []
    chat_ids = []
    ChatID = namedtuple("ChatID", ["id", "tags", "state", "created_at", "manager_id", "user_id"])
    _arr = defaultdict(list)
    states = "all opened closed snoozed".split()
    sorts = "asc desc".split()

    state = state if state in states else ""
    sort_order = sort_order if sort_order in sorts else ""

    if state == "all":
        for s in ["opened", "closed", "snoozed"]:
            _userChats = get_chats(
                state=s, limit=limit, sort_order=sort_order, arr=_arr
            )
            for userChat in _userChats[s]:
                if "managerIds" not in userChat:
                    continue

                # pprint(userChat['userId'])



                # TODO: get user, use the id

                if manager_id in userChat["managerIds"]:
                    # _ids.append(userChat["id"])
                    if not any(chat_id.id == userChat["id"] for chat_id in chat_ids):
                        tags = userChat.get("tags")
                        user_id = userChat['userId']

                        user_profile = next((p for p in _userChats['profile'] if p['user_id'] == user_id), None)
                        chat_user = user_profile

                        chat_ids.append(
                            ChatID(
                                userChat["id"],
                                tags,
                                s,
                                userChat["createdAt"],
                                manager_id,
                                chat_user
                            )
                        )

                    # print([chat_ids[i].id for i in range(len(chat_ids))])
    else:
        _userChats = get_chats(
            state=state, limit=limit, sort_order=sort_order, arr=_arr
        )
        for userChat in _userChats[state]:
            if "managerIds" not in userChat:
                continue

            if manager_id in userChat["managerIds"]:
                if "tags" not in userChat:
                    continue
                tags = userChat.get("tags")
                chat_ids.append(
                    ChatID(userChat["id"], tags, state, userChat["createdAt"], manager_id)
                )

    for chat_id in chat_ids:
        chat_messages = []
        chat_texts = []

        # if any(chat['chat_id'] == chat_id.id for chat in chats):
        #     # check for duplicate chat_id
        #     continue

        _messages = get_chat_messages(chat_id.id)["messages"]

        for message in _messages:
            message_created_at = convert_timestamp_to_date_without_time(
                message["createdAt"]
            )

            if date is not None and message_created_at != date:
                break

            if message["personType"] == "bot":
                continue
            for participant in _userChats["participants"]:
                if message["personId"] == participant["id"]:
                    if "plainText" in message:
                        manager_arrow = ">> " if participant["type"] == "manager" else ""
                        # chat_texts.append(
                        #     f"{manager_arrow} {convert_timestamp_to_date(message['createdAt']).split()[1][0:5]} | {participant['name']}: {message['plainText']}"
                        # )
                        chat_texts.append(
                            f"{manager_arrow}{participant['name']}: {message['plainText']}"
                        )
                        chat_messages.append(
                            {
                                "created_at": convert_timestamp_to_date(
                                    message["createdAt"]
                                ),
                                "participant_name": participant["name"],
                                "participant_id": participant["id"],
                                "chat_message": message["plainText"],
                            }
                        )

        if len(chat_messages) == 0:
            continue

        created_at = chat_messages[0]["created_at"]
        last_message_date = chat_messages[-1]["created_at"]

        chats.append(
            {
                "chat_id": chat_id.id,
                "state": chat_id.state,
                "tags": chat_id.tags,
                "manager_id": chat_id.manager_id,
                "created_at": created_at,
                "last_message_date": last_message_date,
                "messages": chat_messages,
                "texts": chat_texts,
            }
        )

    # TODO: do this on the client side
    # manager_ids = [chat["manager_id"] for chat in chats]
    # if manager_id not in manager_ids:
    #     return {}



    # result["church"] = church_name
    result["manager_id"] = manager_id
    result["count"] = len(chats)
    result["date"] = date
    result["chats"] = chats

    return result


# @app.route("/test", methods=["GET"])
@app.route("/managers/<manager_id>/chats", methods=["GET"])
@app.route("/managers/<manager_id>/chats/<state>", methods=["GET"])
@app.route("/managers/<manager_id>/chats/<state>/<limit>", methods=["GET"])
@app.route("/managers/<manager_id>/chats/<state>/<limit>/<sort_order>", methods=["GET"])
@app.route("/managers/<manager_id>/chats/<state>/<limit>/<sort_order>/<date>",methods=["GET"])
def get_chats_by_manager_id_html(manager_id: str, state: str = "all", limit: str = "50", sort_order: str = "desc", date: str = None) -> dict:
    data = get_chats_by_manager_id(manager_id, state, limit, sort_order, date)
    return render_template("table.html", data=data)


# ------------------------------------------------------


if __name__ == "__main__":
    app.debug = True
    app.run(host="localhost", port=5010)
