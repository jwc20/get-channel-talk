from flask import Flask, redirect, render_template, request, flash, jsonify, send_file
from dotenv import load_dotenv
import os


app = Flask(__name__)

load_dotenv()
app.config["ACCESS_KEY"] = os.getenv("ACCESS_KEY")
app.config["ACCESS_SECRET"] = os.getenv("ACCESS_SECRET")


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.debug = True
    app.run()
