# import necessary libraries
from flask import Flask, render_template, redirect, render_template_string
import scrape_mars
from flask_pymongo import PyMongo
import pymongo
import time

# create instance of Flask app
app = Flask(__name__)

# Initialize PyMongo to work with MongoDBs
conn = 'mongodb://localhost:27017'
client = pymongo.MongoClient(conn)

# Define database and collection
db = client.mars_db
collection = db.items

mongo = PyMongo(app)

# create route that queries the mongo database and pass data into an HTML template
@app.route("/")
def index():
    results = list(collection.find())
    img_url = results[0]['Featured_Image']
    astro_url = results[0]['Image_Site']
    weather = results[0]['Mars_Weather']['Weather']
    tweeter = results[0]['Mars_Weather']['Tweeter']
    cerberus_img = results[0]['Astrogeology']['Images'][0]['img_url']
    schiaparelli_img = results[0]['Astrogeology']['Images'][1]['img_url']
    syrtis_img = results[0]['Astrogeology']['Images'][2]['img_url']
    marineris_img = results[0]['Astrogeology']['Images'][3]['img_url']
    article_title = results[0]['News_Article']['Article_Title']
    article_body = results[0]['News_Article']['Article_Body']
    article_link = results[0]['News_Article']['Article_Link']
    mars_data_html = results[0]['Mars_Facts']['HTML_Table']
    mars_data_link = results[0]['Mars_Facts']['Source']
    
    # return elements to integrate into the html
    return render_template("index.html", img_url = img_url, mars_data_html = mars_data_html, astro_url = astro_url, weather = weather, tweeter = tweeter, cerberus_img = cerberus_img, schiaparelli_img = schiaparelli_img, syrtis_img = syrtis_img, marineris_img = marineris_img, article_title = article_title, article_body = article_body, article_link = article_link, mars_data_link = mars_data_link)

@app.route("/scrape")
def scrape():
    mars_db = mongo.collection
    mars_data = scrape_mars.scrape()
    mars_db.update_one({}, {"$set":mars_data}, upsert = True)
    time.sleep(5)

    return redirect("http://localhost:5000/", code=302)

if __name__ == "__main__":
    app.run(debug=True)
