from flask import Flask, render_template, json, request, redirect, session, url_for
from flask.ext.mysql import MySQL
from werkzeug import generate_password_hash, check_password_hash
import os
import sys
import urlparse

# App Configurations
app = Flask(__name__)

# Register database schemes in URLs.
urlparse.uses_netloc.append('mysql')

if 'DATABASE_URL' in os.environ:
    url = urlparse.urlparse(os.environ['DATABASE_URL'])
else:
    raise Exception("DATABASE_URL not set in os.environ")

# MySQL configurations
app.config['MYSQL_DATABASE_USER'] = url.username
app.config['MYSQL_DATABASE_PASSWORD'] = url.password
app.config['MYSQL_DATABASE_DB'] = url.path[1:]
app.config['MYSQL_DATABASE_HOST'] = url.hostname
app.config['MYSQL_DATABASE_PORT'] = url.port

mysql = MySQL()
mysql.init_app(app)

def create_tables():
    # # Create INSTA_LOC Table
    # try:
    #     conn = mysql.connect()
    #     cursor = conn.cursor()
    #     result = cursor.execute("CREATE TABLE IF NOT EXISTS INSTA_LOC ( INSTA_LOC_ID INT NOT NULL, NAME VARCHAR(100), LAT VARCHAR(20), LNG VARCHAR(20), ADDRESS VARCHAR(200), CATEGORY VARCHAR(200), PRIMARY KEY (INSTA_LOC_ID) );")
    #     # print result, str(cursor.fetchall())
    # except Exception as e:
    #     print "Exception!" + str(e)

    # # Create FOOD_POSTS Table
    # try:
    #     conn = mysql.connect()
    #     cursor = conn.cursor()
    #     result = cursor.execute("CREATE TABLE IF NOT EXISTS FOOD_POSTS ( INSTA_ID VARCHAR(35) NOT NULL, INSTA_TEXT VARCHAR(2200), INSTA_LOC_ID INT NULL, INSTA_IMG_FULL VARCHAR(250), IMAGE_IMG_THUMB VARCHAR(250), USERNAME VARCHAR(20), INSTA_POST_DATE TIMESTAMP, PRIMARY KEY (INSTA_ID), FOREIGN KEY (INSTA_LOC_ID) REFERENCES INSTA_LOC(INSTA_LOC_ID) );")
    #     # print result, str(cursor.fetchall())
    # except Exception as e:
    #     print "Exception!" + str(e)

    conn = mysql.connect()
    cursor = conn.cursor()
    result = cursor.execute("SHOW TABLES")
    print "create_tables complete", result, cursor.fetchall()

def populate_table():
    # Open JSON file
    with open('json_output.json') as data_file: 
        posts = json.load(data_file)
        # Loop through posts and add them to DB
        for item in posts:
            add_item_to_table(item)
            print item["id"] + " added"

    conn = mysql.connect()
    cursor = conn.cursor()
    result = cursor.execute("SELECT * FROM FOOD_POSTS")
    print result, str(cursor.fetchall())
    print "populate_table complete"
    cursor.close()
    conn.close()

def add_item_to_table(item):
    try:
        INSTA_ID = item["id"]
        INSTA_TEXT = item["caption"]["text"]
        # INSTA_LOC_ID = item.location.id
        INSTA_IMG_FULL = item["images"]["standard_resolution"]["url"]
        IMAGE_IMG_THUMB = item["images"]["thumbnail"]["url"]
        USERNAME = item["user"]["username"]
        INSTA_POST_DATE = int(item["created_time"])

        # print "Item INFO:",INSTA_ID,INSTA_TEXT,INSTA_IMG_FULL,IMAGE_IMG_THUMB,USERNAME,INSTA_POST_DATE
        conn = mysql.connect()
        cursor = conn.cursor()
        result = cursor.execute("INSERT INTO FOOD_POSTS (INSTA_ID, INSTA_TEXT, INSTA_IMG_FULL, IMAGE_IMG_THUMB, USERNAME, INSTA_POST_DATE) VALUES (%s, %s, %s, %s, %s, FROM_UNIXTIME(%s))", (INSTA_ID,INSTA_TEXT,INSTA_IMG_FULL,IMAGE_IMG_THUMB,USERNAME,INSTA_POST_DATE))
        conn.commit()
        print "Inserted "+INSTA_ID, result, str(cursor.fetchall())
        
    except Exception as e:
        print "Exception!" + str(e)

    finally:
        try:
            cursor.close()
        except NameError:
            print "Name Error for cursor"
        try:
            conn.close()
        except NameError:
            print "Name Error for conn"

# Routing Definitions
@app.route("/")
def main():
    # return render_template("index.html")
    return redirect(url_for('list'))

@app.route("/list")
def list():
    posts = []
    try:
        conn = mysql.connect()
        cursor = conn.cursor()
        result = cursor.execute("SELECT * FROM FOOD_POSTS")
        posts = cursor.fetchall()
        conn.commit()
    finally:
        cursor.close()
        conn.close()

    return render_template("food-master-list.html", posts=posts, msg="MSG:::"+str(posts))

@app.route("/detail/<insta_id>")
def detail(insta_id):
    post = []
    try:
        conn = mysql.connect()
        cursor = conn.cursor()
        result = cursor.execute("SELECT * FROM FOOD_POSTS WHERE INSTA_ID = %s", [insta_id])
        post = cursor.fetchall()
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    return render_template("food-master-edit.html", post=post, msg=insta_id)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    # create_tables()
    # populate_table()