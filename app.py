from flask import Flask, render_template, json, request, redirect, session
from flask.ext.mysql import MySQL
from werkzeug import generate_password_hash, check_password_hash

# from pprint import pprint

# App Configurations
app = Flask(__name__)

# Load config file for DB user info
with open('config.json') as data_file: 
    config = json.load(data_file)

# Set secret key to use the session module
app.secret_key = config["secret_key"]

# MySQL configurations
app.config['MYSQL_DATABASE_USER'] = config["username"]
app.config['MYSQL_DATABASE_PASSWORD'] = config["password"]
app.config['MYSQL_DATABASE_DB'] = 'FOOD_BLOG'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'

mysql = MySQL()
mysql.init_app(app)

# Routing Definitions
@app.route("/")
def main():
    return render_template("index.html")


if __name__ == "__main__":
    app.run()
