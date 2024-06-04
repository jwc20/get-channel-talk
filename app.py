from flask import Flask, redirect, render_template, request, flash, jsonify, send_file
from dotenv import load_dotenv
import os
import requests

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




if __name__ == "__main__":
    app.debug = True
    app.run()
