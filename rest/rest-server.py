from flask import Flask, request, Response
import jsonpickle, pickle
import json
import platform
import io, os, sys
import pika, redis
import hashlib, requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import selenium.common.exceptions as sel_ex
import sys
import time
import urllib.parse
from retry import retry
import argparse
import logging

# Initialize the Flask application
app = Flask(__name__)
hostname = platform.node()
redisHost = os.getenv("REDIS_HOST") or "localhost"
rabbitMQHost = os.getenv("RABBITMQ_HOST") or "localhost"

print("Connecting to rabbitmq({}) and redis({})".format(rabbitMQHost, redisHost))
redisUserToFoodItems = redis.Redis(host=redisHost, db=1)


logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger()
retry_logger = None

css_thumbnail = "img.Q4LuWd"
css_large = "img.n3VNCb"
css_load_more = ".mye4qd"
selenium_exceptions = (sel_ex.ElementClickInterceptedException, sel_ex.ElementNotInteractableException, sel_ex.StaleElementReferenceException)

def scroll_to_end(wd):
    wd.execute_script("window.scrollTo(0, document.body.scrollHeight);")

@retry(exceptions=KeyError, tries=6, delay=0.1, backoff=2, logger=retry_logger)
def get_thumbnails(wd, want_more_than=0):
    wd.execute_script("document.querySelector('{}').click();".format(css_load_more))
    thumbnails = wd.find_elements_by_css_selector(css_thumbnail)
    n_results = len(thumbnails)
    if n_results <= want_more_than:
        raise KeyError("no new thumbnails")
    return thumbnails

@retry(exceptions=KeyError, tries=6, delay=0.1, backoff=2, logger=retry_logger)
def get_image_src(wd):
    actual_images = wd.find_elements_by_css_selector(css_large)
    sources = []
    for img in actual_images:
        src = img.get_attribute("src")
        if src.startswith("http") and not src.startswith("https://encrypted-tbn0.gstatic.com/"):
            sources.append(src)
    if not len(sources):
        raise KeyError("no large image")
    return sources

@retry(exceptions=selenium_exceptions, tries=6, delay=0.1, backoff=2, logger=retry_logger)
def retry_click(el):
    el.click()

def get_images(wd, start=0, n=20, out=None):
    thumbnails = []
    count = len(thumbnails)
    while count < n:
        scroll_to_end(wd)
        try:
            thumbnails = get_thumbnails(wd, want_more_than=count)
        except KeyError as e:
            logger.warning("cannot load enough thumbnails")
            break
        count = len(thumbnails)
    sources = []
    for tn in thumbnails:
        try:
            retry_click(tn)
        except selenium_exceptions as e:
            logger.warning("main image click failed")
            continue
        sources1 = []
        try:
            sources1 = get_image_src(wd)
        except KeyError as e:
            pass
            # logger.warning("main image not found")
        if not sources1:
            tn_src = tn.get_attribute("src")
            if not tn_src.startswith("data"):
                logger.warning("no src found for main image, using thumbnail")          
                sources1 = [tn_src]
            else:
                logger.warning("no src found for main image, thumbnail is a data URL")
        for src in sources1:
            if not src in sources:
                sources.append(src)
                if out:
                    print(src, file=out)
                    out.flush()
        if len(sources) >= n:
            break
    return sources

def google_image_search(wd, query, safe="off", n=20, opts='', out=None):
    search_url_t = "https://www.google.com/search?safe={safe}&site=&tbm=isch&source=hp&q={q}&oq={q}&gs_l=img&tbs={opts}"
    search_url = search_url_t.format(q=urllib.parse.quote(query), opts=urllib.parse.quote(opts), safe=safe)
    wd.get(search_url)
    sources = get_images(wd, n=n, out=out)
    return sources

def getUrl(query, nImages):  
    opts = Options()
    opts.add_argument('--no-sandbox')
    opts.add_argument("--headless")
    # opts.add_argument("--blink-settings=imagesEnabled=false")
    wd = webdriver.Chrome(options=opts)
    
    sources = google_image_search(wd, query, safe="off", n=nImages, opts="", out=sys.stdout)
    return sources[0]

class Item:
    def __init__(self, name, description, price):
        self.foodName=name
        self.description=description
        self.price=price
        self.url=None

@app.route("/", methods=["GET"])
def hello():
    log(
        "logs",
        hostname + ".rest.info",
        "Food Recommender",
    )
    return "<h1>Food Recommender</h1><p> Use a valid endpoint </p>"

@app.route('/find', methods=['POST'])
def scanUrlImage():
    log(
        "logs",
        hostname + ".rest.info",
        request.data,
    )
    req=request.get_json(force=True)
    user=req['user']
    radius=req['radius']
    lat=req['lat']
    lon=req['lon']

    log(
        "logs",
        hostname + ".rest.info",
        "Finding food items options nearby...",
    )

    body={
        'user': user,
        'radius' : radius,
        'lat' : lat,
        'lon'   : lon
    }
    pickledBody=pickle.dumps(body)
    enqueue("toWorker", pickledBody)
    log(
        "logs",
        hostname + ".rest.info",
        "Latitude-Longitude pair added to RabbitMQ",
    )
    return Response(response=pickledBody, status=200, mimetype="application/json")

@app.route("/getNext/<user>", methods=["GET"])
def getNext(user):
    log(
        "logs",
        hostname + ".rest.info",
        "Finding next food item...",
    )

    foodItem=redisUserToFoodItems.spop(user)
    item=pickle.loads(foodItem)
    item.url=getUrl(item.foodName, 1)
    return Response(response=foodItem, status=200, mimetype="application/json")


def enqueue(queue_name, obj):
    rabbitMQ_connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=rabbitMQHost)
    )
    channel = rabbitMQ_connection.channel()
    channel.queue_declare(queue=queue_name)
    channel.exchange_declare(exchange=queue_name, exchange_type="direct")
    channel.basic_publish(exchange=queue_name, routing_key="info", body=obj)
    print(" [x] Sent %r:%r" % ("info", obj))
    rabbitMQ_connection.close()


def log(queue_name, routing_key, message):
    rabbitMQ_connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=rabbitMQHost)
    )
    channel = rabbitMQ_connection.channel()
    channel.queue_declare(queue=queue_name)
    channel.exchange_declare(exchange=queue_name, exchange_type="topic")
    channel.basic_publish(exchange=queue_name, routing_key=routing_key, body=message)
    rabbitMQ_connection.close()


# start flask app
app.run(host="0.0.0.0", port=5000)