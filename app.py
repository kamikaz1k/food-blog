from flask import Flask, render_template, json, request, redirect, session, url_for
import os
import re
import pdb
from flask_sqlalchemy import SQLAlchemy

if 'DATABASE_URL' not in os.environ:
    raise Exception("DATABASE_URL not set in os.environ")
    
# App Configurations
app = Flask(__name__)

# MySQL configurations
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)

# mysql = MySQL()
# mysql.init_app(app)

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
    #     result = cursor.execute("CREATE TABLE IF NOT EXISTS FOOD_POSTS ( INSTA_ID VARCHAR(50) NOT NULL, INSTA_TEXT VARCHAR(2200), INSTA_LOC_ID INT NULL, INSTA_IMG_FULL VARCHAR(250), INSTA_IMG_THUMB VARCHAR(250), USERNAME VARCHAR(20), INSTA_POST_DATE TIMESTAMP, INSTA_LOC_NAME VARCHAR(100) NOT NULL DEFAULT '', FOOD_NAME VARCHAR(100), INSTA_IMG_MED VARCHAR(250), PRIMARY KEY (INSTA_ID), FOREIGN KEY (INSTA_LOC_ID) REFERENCES INSTA_LOC(INSTA_LOC_ID) );")
    #     # print result, str(cursor.fetchall())
    # except Exception as e:
    #     print "Exception!" + str(e)

    db.create_all()
    print "create_tables complete", db.metadata.tables.items()

def populate_table(filename='json_output.json'):
    # Open JSON file
    with open(filename) as data_file: 
        posts = json.load(data_file)
        # Loop through posts and add them to DB
        for item in posts:
            add_item_to_table(item)
            print item["id"] + " added"

    conn = mysql.connect()
    cursor = conn.cursor()
    result = cursor.execute("SELECT * FROM FOOD_POSTS")
    # print result, str(cursor.fetchall())
    # print "populate_table complete"
    cursor.close()
    conn.close()

def add_item_to_table(item):
    try:
        INSTA_ID = item["code"]
        INSTA_TEXT = item["caption"]["text"] if item["caption"] else ""
        # INSTA_LOC_ID = item.location.id
        INSTA_LOC_NAME = item["location"]["name"] if item["location"] else ""
        INSTA_IMG_FULL = item["images"]["standard_resolution"]["url"] if item["images"] and item["images"]["standard_resolution"] else ""
        INSTA_IMG_THUMB = item["images"]["thumbnail"]["url"] if item["images"] and item["images"]["thumbnail"] else ""
        INSTA_IMG_MED = item["images"]["low_resolution"]["url"] if item["images"] and item["images"]["low_resolution"] else ""
        USERNAME = item["user"]["username"]
        INSTA_POST_DATE = int(item["created_time"])

        # print "Item INFO:",INSTA_ID,INSTA_TEXT,INSTA_IMG_FULL,INSTA_IMG_THUMB,USERNAME,INSTA_POST_DATE
        conn = mysql.connect()
        cursor = conn.cursor()
        result = cursor.execute("INSERT INTO FOOD_POSTS "
                                "(INSTA_ID, INSTA_TEXT, INSTA_IMG_FULL, INSTA_IMG_THUMB, USERNAME, INSTA_POST_DATE, INSTA_LOC_NAME, INSTA_IMG_MED) "
                                "VALUES (%s, %s, %s, %s, %s, FROM_UNIXTIME(%s), %s, %s)", 
                                ( INSTA_ID, INSTA_TEXT, INSTA_IMG_FULL, INSTA_IMG_THUMB, USERNAME, INSTA_POST_DATE, INSTA_LOC_NAME, INSTA_IMG_MED))
        conn.commit()
        print "Inserted "+INSTA_ID, result, str(cursor.fetchall())
        
    except Exception as e:
        print "Exception! for ",INSTA_ID
        print str(item)
        print str(e)

    finally:
        try:
            cursor.close()
        except NameError:
            print "Name Error for cursor"
        try:
            conn.close()
        except NameError:
            print "Name Error for conn"

def populate_locations():
    # Open JSON file
    with open('json_output.json') as data_file: 
        posts = json.load(data_file)
        # Loop through posts and add them to DB
        for item in posts:
            add_location_to_item(item)
            print item["id"] + " updated"


def add_location_to_item(item):
    try:
        INSTA_ID = item["id"]
        INSTA_LOC_NAME = item["location"]["name"]

        # print "Item INFO:",INSTA_ID,INSTA_TEXT,INSTA_IMG_FULL,INSTA_IMG_THUMB,USERNAME,INSTA_POST_DATE
        conn = mysql.connect()
        cursor = conn.cursor()
        result = cursor.execute("UPDATE FOOD_POSTS SET INSTA_LOC_NAME=%s WHERE INSTA_ID=%s", (INSTA_LOC_NAME, INSTA_ID))
        conn.commit()
        print "Inserted "+INSTA_ID, result, str(cursor.fetchall())
        
    except Exception as e:
        print "Exception! for " + INSTA_ID + " " + INSTA_LOC_NAME + " -> " + str(e)

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
    return redirect(url_for('feed'))

@app.route("/list")
def list():
    LIMIT = 10
    page = int(request.args.get('page', '1'))

    try:
        paginated_posts = FoodPost.query.order_by(FoodPost.insta_post_date.desc()).paginate(page, LIMIT, False)
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
    page = int(request.args.get('page', '1'))

    # Setup Query Params
    LIMIT = 10

    try:
        paginated_posts = FoodPost.query.order_by(FoodPost.insta_post_date.desc()).paginate(page, LIMIT, False)
    except Exception as e:
        return render_template("error.html", title="QUERY Error", msg=str(e))
    # pdb.set_trace()

    return render_template("search-post-results.html",
                            posts=paginated_posts.items,
                            pagination=paginated_posts,
                            msg="has_next {} | has_prev {} |".format(paginated_posts.has_next, paginated_posts.has_prev))

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
    FOOD_NAME = "%{}%".format(request.args.get("food_name",""))
    USERNAME = "%{}%".format(request.args.get("poster",""))
    page = int(request.args.get('page', '1'))

    # Setup Query Params
    LIMIT = 10

    try:
        paginated_posts = FoodPost.query.order_by(FoodPost.insta_post_date.desc()) \
                                    .filter(FoodPost.insta_loc_name.ilike(LOCATION), FoodPost.food_name.ilike(FOOD_NAME), FoodPost.username.ilike(USERNAME)) \
                                    .paginate(page, LIMIT, False)
    except Exception as e:
        return render_template("error.html", title="QUERY Error", msg=str(e))

    return render_template("search-post-results.html",
                            posts=paginated_posts.items,
                            pagination=paginated_posts,
                            page=page,
                            location_name=LOCATION[1:-1],
                            food_name=FOOD_NAME[1:-1],
                            msg="LOCATION: {} | FOOD_NAME: {} | USERNAME: {} | Page: {}".format(LOCATION, FOOD_NAME, USERNAME, page))

@app.route("/post/<insta_id>")
def post(insta_id):
    
    post = []
    try:
        post = FoodPost.query.filter_by(insta_id=insta_id).first()
    except Exception as e:
        return render_template("error.html", title="QUERY Error", msg=str(e))

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
                            location_tags=location_tags, 
                            msg='location_tags + "::"' + str(location_tags))

if __name__ == "__main__":
    # print "DATABASE_URL: " + url
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

    create_tables()
    # populate_table("brianeatss_media_dump.json")
    # populate_table("kamikaz1_k_media_dump.json")
    # populate_table()
    # populate_locations()