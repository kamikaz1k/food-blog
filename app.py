from flask import Flask, render_template, json, request, redirect, session, url_for, flash
import os
import re
import pdb
import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import load_only

from insta_scraper import call_main as scraper

import threading

if 'DATABASE_URL' not in os.environ:
    raise Exception("DATABASE_URL not set in os.environ")

# App Configurations
app = Flask(__name__)

app.secret_key = os.environ.get('SECRET_KEY', 'a_sekret_key')

# MySQL configurations
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_POOL_RECYCLE'] = int(os.environ['DATABASE_POOL_RECYCLE']) # Needs to be < 60 for ClearDB/Heroku
app.config['SQLALCHEMY_POOL_SIZE'] = int(os.environ['DATABASE_POOL_SIZE']) # Needs to be =< 4 for ClearDB/Heroku
app.config['SQLALCHEMY_ECHO'] = False
app.config['WORKER_QUEUE'] = []
app.config['WORKER_RUNNING'] = False
db = SQLAlchemy(app)

db.create_all()

class FoodPost(db.Model):
    __tablename__ = 'FOOD_POSTS'
    insta_id = db.Column(db.String(50), primary_key=True)
    insta_text = db.Column(db.String(2200))
    insta_loc_id = db.Column(db.Integer, db.ForeignKey('INSTA_LOC.insta_loc_id'), nullable=True)
    insta_img_full = db.Column(db.String(250))
    insta_img_thumb = db.Column(db.String(250))
    insta_img_med = db.Column(db.String(250))
    username = db.Column(db.String(20))
    insta_post_date = db.Column(db.TIMESTAMP, server_default='0')
    insta_loc_name = db.Column(db.String(100))
    food_name = db.Column(db.String(100), default="")

    def __init__(self, insta_id, insta_text, insta_loc_id, insta_img_full, insta_img_thumb, insta_img_med, username, insta_post_date, insta_loc_name, food_name):
        self.insta_id = insta_id
        self.insta_text = insta_text
        self.insta_loc_id = insta_loc_id
        self.insta_img_full = insta_img_full
        self.insta_img_thumb = insta_img_thumb
        self.insta_img_med = insta_img_med
        self.username = username
        self.insta_post_date = insta_post_date
        self.insta_loc_name = insta_loc_name
        self.food_name = food_name

    def __repr__(self):
        return "<FoodPost(insta_id='%s', insta_text='%s', insta_loc_id='%s', insta_img_full='%s', insta_img_thumb='%s', insta_img_med='%s', username='%s', insta_post_date='%s', insta_loc_name='%s', food_name='%s')>" % (
                self.insta_id, self.insta_text, self.insta_loc_id, self.insta_img_full, self.insta_img_thumb, self.insta_img_med, self.username, self.insta_post_date, self.insta_loc_name, self.food_name)

class InstaLoc(db.Model):
    __tablename__ = 'INSTA_LOC'
    insta_loc_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    lat = db.Column(db.String(20))
    lng = db.Column(db.String(20))
    address = db.Column(db.String(200), default="")
    category = db.Column(db.String(200), default="")

    def __init__(self, insta_loc_id, name, lat, lng, address, category):
        self.insta_loc_id = insta_loc_id
        self.name = name
        self.lat = lat
        self.lng = lng
        self.address = address
        self.category = category

    def __repr__(self):
        return "<FoodPost(insta_loc_id='%s', name='%s', lat='%s', lng='%s', address='%s', category='%s')>" % (
                self.insta_loc_id, self.name, self.lat, self.lng, self.address, self.category)

def parse_page_number(val):
    try:
        return int(val)
    except Exception as e:
        return -1

def create_tables():
    db.create_all()
    print "create_tables complete", db.metadata.tables.items()

def populate_table(filename, username):

    if filename is None or username is None:
        return

    # Get list of IDs first
    try:
        user_posts = FoodPost.query.filter(FoodPost.username.ilike(username)).options(load_only("insta_id"))
        user_posts_ids = []
        for item in user_posts:
            user_posts_ids.append(item.insta_id)

    except Exception as e:
        app.logger.error("Exception in user_posts query after sync:")
        app.logger.error(e)

    # Open JSON file
    with open(filename) as data_file:
        errors = 0;
        # Loop through posts and add them to DB
        for line in data_file:
            post = json.loads(line)
            try:
                if post["code"] in user_posts_ids:
                    errors += 1
                    raise Exception("Post already exists")
                add_item_to_table(post)
                app.logger.debug(post["id"] + " added")
            except Exception as e:
                app.logger.error(post["id"] + " was NOT added. No. of errors: {}".format(errors))
                app.logger.error(e)
                # e.orig is for the duplicate key error

    # Then delete the file
    app.logger.debug("Removing json dump file: {}".format(filename))
    os.remove(filename)

def add_item_to_table(item):
    INSTA_ID = item["code"]
    INSTA_TEXT = item["caption"]["text"] if item["caption"] else ""
    # INSTA_LOC_ID = item.location.id
    INSTA_LOC_NAME = item["location"]["name"] if item["location"] else ""
    INSTA_IMG_FULL = item["images"]["standard_resolution"]["url"] if item["images"] and item["images"]["standard_resolution"] else ""
    INSTA_IMG_THUMB = item["images"]["thumbnail"]["url"] if item["images"] and item["images"]["thumbnail"] else ""
    INSTA_IMG_MED = item["images"]["low_resolution"]["url"] if item["images"] and item["images"]["low_resolution"] else ""
    USERNAME = item["user"]["username"]
    INSTA_POST_DATE = datetime.datetime.utcfromtimestamp(
        int(item["created_time"])
    )

    new_entry = FoodPost(insta_id=INSTA_ID,
                        insta_text=INSTA_TEXT,
                        insta_loc_id=None,
                        insta_img_full=INSTA_IMG_FULL,
                        insta_img_thumb=INSTA_IMG_THUMB,
                        insta_img_med=INSTA_IMG_MED,
                        username=USERNAME,
                        insta_post_date=INSTA_POST_DATE,
                        insta_loc_name=INSTA_LOC_NAME,
                        food_name="")

    try:
        db.session.add(new_entry)
        db.session.commit()
    except:
        db.session.rollback()
        raise
    # finally:
    #     db.session.close()

# Routing Definitions
@app.route("/")
def main():
    return redirect(url_for('feed'))

@app.route("/list")
def list():
    LIMIT = 10
    PAGE_NUM = int(request.args.get('page', 1))
    if PAGE_NUM < 1:
        return redirect(url_for("list", page=1))

    try:
        paginated_posts = FoodPost.query.order_by(FoodPost.insta_post_date.desc()).paginate(PAGE_NUM, LIMIT, False)
    except Exception as e:
        return render_template("error.html", title="QUERY Error", msg=str(e))

    return render_template("food-master-list.html",
                           posts=paginated_posts.items,
                           pagination=paginated_posts)

@app.route("/detail/<insta_id>")
def detail(insta_id):
    try:
        post = FoodPost.query.filter_by(insta_id=insta_id).first()
    except Exception as e:
        return render_template("error.html", title="QUERY Error", msg=str(e))

    return render_template("food-master-edit.html", post=post, msg=insta_id)

@app.route("/feed")
def feed():
    LIMIT = 10
    PAGE_NUM = parse_page_number(request.args.get('page', 1))
    if PAGE_NUM < 1:
        return redirect(url_for("feed", page=1))

    try:
        paginated_posts = FoodPost.query.order_by(FoodPost.insta_post_date.desc()).paginate(PAGE_NUM, LIMIT, False)
    except Exception as e:
        return render_template("error.html", title="QUERY Error", msg=str(e))

    return render_template("feed-results.html",
                            posts=paginated_posts.items,
                            pagination=paginated_posts)

@app.route("/save/<insta_id>", methods=["POST"])
def save(insta_id):
    # Get all the form details
    # Only need to update FOOD_NAME and INSTA_LOC_NAME
    FOOD_NAME = request.form['FOOD_NAME']
    INSTA_LOC_NAME = request.form['INSTA_LOC_NAME']

    if insta_id and FOOD_NAME and INSTA_LOC_NAME:
        try:
            post = FoodPost.query.filter_by(insta_id=insta_id).first()
            post.food_name = FOOD_NAME
            post.insta_loc_name = INSTA_LOC_NAME
            post.insta_post_date = post.insta_post_date
            db.session.commit()
            return redirect(url_for("list"))
        except Exception as e:
            return render_template("error.html", title="QUERY Error", msg=str(e))
    else:
        return render_template("error.html", title="FORM Error", msg="Either the insta_id or FOOD_NAME or INSTA_LOC_NAME was missing")

@app.route("/search")
def search():
    # Valid search params
    LOCATION = "%{}%".format(request.args.get("location_name",""))
    TEXT = "%{}%".format(request.args.get("food-text",""))
    FOOD_NAME = "%{}%".format(request.args.get("food_name",""))
    USERNAME = "%{}%".format(request.args.get("poster",""))

    PAGE_NUM = parse_page_number(request.args.get('page', 1))
    if PAGE_NUM < 1:
        return redirect(url_for("search", page=1, location_name=LOCATION, food_name=FOOD_NAME, poster=USERNAME))

    # Setup Query Params
    LIMIT = 10

    try:
        paginated_posts = FoodPost.query.order_by(FoodPost.insta_post_date.desc()) \
                                    .filter(FoodPost.insta_loc_name.ilike(LOCATION),
                                            FoodPost.food_name.ilike(FOOD_NAME),
                                            FoodPost.insta_text.ilike(TEXT),
                                            FoodPost.username.ilike(USERNAME)) \
                                    .paginate(PAGE_NUM, LIMIT, False)
    except Exception as e:
        return render_template("error.html", title="QUERY Error", msg=str(e))

    query_string = "&".join(["{}={}".format(k, request.args.get(k)) for k in request.args.keys()])

    if query_string != "":
        query_string = "&" + query_string

    return render_template("search-post-results.html",
                            posts=paginated_posts.items,
                            pagination=paginated_posts,
                            query_string=query_string)

@app.route("/post/<insta_id>")
def post(insta_id):

    post = []
    try:
        post = FoodPost.query.filter_by(insta_id=insta_id).first()
    except Exception as e:
        return render_template("error.html", title="QUERY Error", msg=str(e))

    if post is None:
        return render_template("error.html", title="Post not found...", msg="Post not found...how did you get here?")

    # Parse all the explore tag options
    # For Location split the words
    # And filter out the empty strings
    location_tags = re.split("(?=[^-])\W+", post.insta_loc_name)
    location_tags = [k for k in location_tags if k is not ''] # For some reason it is not working in flask, but it is on cmd

    # For Name split the words
    # And filter out the empty strings
    if post.food_name:
        name_tags = re.split("(?=[^-])\W+", post.food_name)
        name_tags = [k for k in name_tags if k is not '']
    else:
        name_tags = []

    # Hash tags
    # re.findall("#\w+",posts[0][1])

    return render_template("view-post.html",
                            food_name=post.food_name,
                            food_caption=post.insta_text,
                            location_name=post.insta_loc_name,
                            image_link=post.insta_img_full,
                            post_date=post.insta_post_date,
                            username=post.username,
                            post_id=post.insta_id,
                            name_tags=name_tags,
                            location_tags=location_tags)

@app.route("/userSync", methods=["GET","POST"])
def userSync():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        queueScrape(username, password)
        flash("Starting process for {}".format(username))
        return redirect(url_for('userSync'))
    else:
        return render_template("user-sync.html")

def runScraper(username, password, populate_db, cb):
    app.logger.debug("Starting worker...")
    filename = False
    try:
        filename = scraper(username, password)
        app.logger.debug("Output filename - {}".format(filename))
    except Exception as e:
        app.logger.error(str(e))
    # Callback after jobs done
    app.logger.debug("Worker done.")

    if filename:
        populate_db(filename, username)

    cb()

def queueScrape(username, password):
    # If something is running, or if there's something queued
    # queue this job
    if app.config['WORKER_RUNNING'] or len(app.config['WORKER_QUEUE']):
        app.config['WORKER_QUEUE'].append({ "username": username, "password": password })
        app.logger.debug("Queueing scrape request...")
        app.logger.debug(app.config['WORKER_QUEUE'])
    # If nothing is running, and queue is empty
    # start job without queueing
    else:
        app.config['WORKER_RUNNING'] = True
        t = threading.Thread(target=runScraper, args=(username,password,populate_table,consumeScrape))
        t.start()

def consumeScrape():
    app.config['WORKER_RUNNING'] = False

    # If there are queued items, start the head
    if len(app.config['WORKER_QUEUE']):

        username = app.config['WORKER_QUEUE'][0]['username']
        password = app.config['WORKER_QUEUE'][0]['password']

        app.config['WORKER_QUEUE'] = app.config['WORKER_QUEUE'][1:]

        app.config['WORKER_RUNNING'] = True
        t = threading.Thread(target=runScraper, args=(username,password,populate_table,consumeScrape))
        t.start()
    # Otherwise, do nothing
    else:
        app.logger.debug("Queue is empty.")

if __name__ == "__main__":

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

    # create_tables()
    # populate_table()