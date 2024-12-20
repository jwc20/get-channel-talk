from flask import Flask, redirect, render_template, request, flash, jsonify, send_file
from dotenv import load_dotenv
import os
import requests
from typing import DefaultDict, List, Dict
from collections import defaultdict, namedtuple
from datetime import datetime, timezone, timedelta
import urllib.parse
import emoji


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

    # TODO: Add pagination

    response = requests.get(
        "http://api.channel.io/open/v5/user-chats/"
        + chatId
        + "/messages?sortOrder=asc&limit=50",
        headers=headers,
        json=True,
    )
    response.encoding = "utf-8"
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

    return arr


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
    ChatID = namedtuple("ChatID", ["id", "tags", "state", "created_at", "manager_id"])
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

                if manager_id in userChat["managerIds"]:
                    # _ids.append(userChat["id"])
                    if not any(chat_id.id == userChat["id"] for chat_id in chat_ids):
                        tags = userChat.get("tags")
                        chat_ids.append(
                            ChatID(
                                userChat["id"],
                                tags,
                                s,
                                userChat["createdAt"],
                                manager_id,
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
                tags = userChat[tags]
                chat_ids.append(
                    ChatID(userChat["id"], tags, s, userChat["createdAt"], manager_id)
                )

    for chat_id in chat_ids:
        chat_messages = []
        chat_texts = []

        _messages = get_chat_messages(chat_id.id)["messages"]

        for message in _messages:
            message_created_at = convert_timestamp_to_date_without_time(
                message["createdAt"]
            )

            if date is not None and message_created_at != date:
                break

            if message["personType"] == "bot":
                continue

            remove_list = [
                "사용문의",
                "설치형 (CS 교적/재정,비품관리, 종교인회계)",
                "웹 (NEW 워칭, V6, 가정교회 360, 온라인행정)",
                "프로그램 or 홈페이지 구축 상담",
                "사용문의 메뉴로 돌아가기",
                "PC설치형 교적/재정 프로그램",
                "재정 문의",
                "앱 & 모바일 (스마트 성도 앱, 스마트요람)",
                "🖥️ 사용문의",
                "💻 설치형 (CS 교적/재정,비품관리, 종교인회계)",
                "🌐 웹 (NEW 워칭, V6, 가정교회 360, 온라인행정)",
                "✨ 프로그램 or 홈페이지 구축 상담",
                "🔙사용문의 메뉴로 돌아가기",
                "PC설치형 교적/재정 프로그램",
                "재정 문의",
                "📱 앱 & 모바일 (스마트 성도 앱, 스마트요람)",
                "교적 문의",
                "상담원 연결하기",
            ]

            for participant in _userChats["participants"]:
                if message["personId"] == participant["id"]:
                    if "plainText" in message:
                        plaintext = message["plainText"]  # chat message

                        cleaned_text = ""
                        for char in plaintext:
                            if not (
                                0x1F300 <= ord(char) <= 0x1F9FF  # Emoticons
                                or 0x2600 <= ord(char) <= 0x26FF  # Misc symbols
                                or 0x2700 <= ord(char) <= 0x27BF  # Dingbats
                                or 0xFE00 <= ord(char) <= 0xFE0F  # Variation selectors
                                or 0x1F900
                                <= ord(char)
                                <= 0x1F9FF  # Supplemental symbols
                                or 0x1F600 <= ord(char) <= 0x1F64F
                            ):  # Emoticons
                                cleaned_text += char

                        cleaned_text = cleaned_text.strip()

                        cleaned_text = cleaned_text.replace("  ", " ")
                        if cleaned_text in remove_list:
                            continue

                        # Skip if message is empty after cleaning
                        if not cleaned_text:
                            continue

                        # add arrow to indicate manager
                        is_manager = participant["type"] == "manager"
                        manager_arrow = ">> " if is_manager else ""

                        # Check if previous message exists and was from a manager
                        prev_was_manager = len(chat_texts) > 0 and chat_texts[
                            -1
                        ].startswith(">> ")

                        # Add newlines based on message sender type
                        if is_manager:
                            if (
                                not prev_was_manager
                            ):  # If previous message was from user, add newline before
                                chat_texts.append("")
                            chat_texts.append(f"{manager_arrow}{cleaned_text}")
                        else:  # User message
                            if (
                                prev_was_manager
                            ):  # If previous message was from manager, add newline before
                                chat_texts.append("")
                            chat_texts.append(f"{manager_arrow}{cleaned_text}")

                        chat_messages.append(
                            {
                                "created_at": convert_timestamp_to_date(
                                    message["createdAt"]
                                ),
                                "participant_name": participant["name"],
                                "participant_id": participant["id"],
                                "chat_message": cleaned_text,
                            }
                        )

        if len(chat_messages) == 0:
            continue

        created_at = chat_messages[0]["created_at"]
        last_message_date = chat_messages[-1]["created_at"]

        chats.append({
            "chat_id": chat_id.id,
            "state": chat_id.state,
            "tags": chat_id.tags,
            "manager_id": chat_id.manager_id,
            "created_at": created_at,
            "last_message_date": last_message_date,
            "messages": chat_messages,
            "texts": chat_texts,
            "participants": [  # Add this new field
                {
                    "name": participant["name"],
                    "type": participant["type"]
                } 
                for participant in _userChats["participants"] 
                if any(msg["participant_id"] == participant["id"] for msg in chat_messages)
            ]
        })

    result["manager_id"] = manager_id
    result["count"] = len(chats)
    result["date"] = date
    result["chats"] = chats

    return result


@app.route("/managers/<manager_id>/chats", methods=["GET"])
@app.route("/managers/<manager_id>/chats/<state>", methods=["GET"])
@app.route("/managers/<manager_id>/chats/<state>/<limit>", methods=["GET"])
@app.route("/managers/<manager_id>/chats/<state>/<limit>/<sort_order>", methods=["GET"])
@app.route(
    "/managers/<manager_id>/chats/<state>/<limit>/<sort_order>/<date>", methods=["GET"]
)
def get_chats_by_manager_id_html(
    manager_id: str,
    state: str = "all",
    limit: str = "100",
    sort_order: str = "desc",
    date: str = None,
) -> dict:
    data = get_chats_by_manager_id(manager_id, state, limit, sort_order, date)
    return render_template("table.html", data=data)


# ------------------------------------------------------


if __name__ == "__main__":
    app.debug = True
    app.run(host="localhost", port=50010)
