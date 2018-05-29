import time
from bs4 import BeautifulSoup as bs
import requests
from splinter import Browser

import tweepy
from config import api_key as consumer_key
from config import api_secret as consumer_secret
from config import access_token as access_token
from config import access_secret as access_token_secret

import pandas as pd
import shutil

#Tweepy OAuth dependencies
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth, parser = tweepy.parsers.JSONParser())


def scrape():
    '''Create a function to be used in the control file to execute all the web scraping'''

    #Initial URL
    mars_url = "https://mars.nasa.gov/news/"

    print("getting the mars_url")

    #Pulling down URL for Mars News site
    response = requests.get(mars_url)

    #Creating a beautiful soup object for the mars news site
    soup = bs(response.text, 'lxml')
    
    #Grabbing necessary content
    news_title = soup.find('div', class_= 'content_title').text.strip()
    news_body = soup.find('div', class_ = 'image_and_description_container').text.strip()
    news_href = soup.find('div', class_= 'content_title').a['href']

    #defining the path for the next web scrape
    jpl_url = "https://www.jpl.nasa.gov/spaceimages/?search=&category=Mars"

    print("visiting the jpl_url")
    
    #create a splinter browser
    executable_path = {'executable_path': 'chromedriver.exe'}
    browser = Browser('chrome', **executable_path, headless=False)

    #Use the browser to visit the specified URL
    browser.visit(jpl_url)   

    #sleep one half second
    time.sleep(.5)

    #follow the link for the button with "Full Image" text
    browser.click_link_by_partial_text('FULL IMAGE')

    #sleep one half second
    time.sleep(.5)

    print("finding the featured image")
    
    #find the featured image url by looping through the img tags and pulling out the one only with teh class of "fancybox-image"
    results = browser.find_by_tag('img')
    time.sleep(.5)
    for result in results:
        if result['class'] == "fancybox-image":
            featured_image_url = result['src']

    #Defining the target user
    target_user = "marswxreport"

    print("finding the tweets")

    #gettig all the tweets from the target user
    public_tweets = api.user_timeline(target_user)

    #sleep one half second
    time.sleep(.5)

    #finding the last tweet & saving as a variable called "mars_weather"
    mars_weather = public_tweets[0]['text']

    # creating an object to hold the url data
    mars_facts_url = "http://space-facts.com/mars/"

    print("Reading the Mars Data site")
    
    # Reading the url into a dataframe
    mars_data = pd.read_html(mars_facts_url)

    # taking the dataframe out of the list
    mars_df = mars_data[0]

    #renaming the columns
    mars_df = mars_df.rename(columns = {0:'Metrics', 1: 'Parameters'})

    # resetting the index
    mars_df.set_index('Metrics', inplace = True)

    #convert mars dataframe to html
    mars_data_html = mars_df.to_html()

    #astrogeology url
    astro_url = "https://astrogeology.usgs.gov/search/results?q=hemisphere+enhanced&k1=target&v1=Mars"
    
    print("Getting the astrogeology data")

    #Reading the url
    response = requests.get(astro_url)

    # turning the htrml response to a Beautiful Soup object
    soup = bs(response.text, 'lxml')
    
    #setting the base path for image scraping
    base_path = 'https://astrogeology.usgs.gov'

    print("getting the thumnail image URLs")

    #findings the links to the thumbnails
    thumb_urls = []
    img_url = soup.find_all("img", class_= "thumb")
    for url in img_url:
        thumb_urls.append(('https://astrogeology.usgs.gov' + url['src']))
    
    print("downloading each of the thumbnails")

    #downloading each of the thumbnails
    i = 1
    for url in thumb_urls:
        response = requests.get(url, stream = True)
        with open(f"templates\Thumb{i}.png", 'wb') as out_file:
            shutil.copyfileobj(response.raw, out_file)
            time.sleep(1)
        i += 1

    print("getting the links for the enhanced images")

    #go to the specified path, find the links to the images, and put in a list.
    image_links = []
    results = soup.find_all('div', class_='item')
    time.sleep(.5)
    for result in results:
        tag = base_path + result.a['href']
        image_links.append(tag)

    
    print("Getting the astrogeology data")

    #visit each url and grab the required information
    hemisphere_image_urls = []
    for link in image_links:
        hemisphere = link.split("/")[-1][:-9].capitalize()
        response = requests.get(link)
        soup = bs(response.text, 'lxml')
        time.sleep(.5)
        items = soup.find_all('a', target = "_blank")
        for item in items:
            small_dict = {}
            if item.text == "Original":
                small_dict['img_url'] = small_dict.get('img_url', item['href'])
                small_dict["Hemisphere"] = small_dict.get("Hemisphere", hemisphere)
                hemisphere_image_urls.append(small_dict)

    print("creating the mars_dict object")
    
    # create a dictionary to hold the content from the scraping function
    mars_dict = {
        "News_Site": mars_url,
        "News_Article": {
            "Article_Title": news_title,
            "Article_Body": news_body,
            "Article_Link": news_href
            },
        "Image_Site": jpl_url,
        "Featured_Image": featured_image_url,
        "Mars_Weather": {
            "Tweeter": target_user,
            "Weather": mars_weather
            },
        "Mars_Facts": {
            "Source": mars_facts_url,
            "HTML_Table": mars_data_html,
            },
        "Astrogeology": {
            "Source": astro_url,
            "Images": hemisphere_image_urls
            }
        }

    #return a dictionary for the function to use
    return mars_dict