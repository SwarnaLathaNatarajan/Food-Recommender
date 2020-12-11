#
# Worker server
#
import jsonpickle
import platform
import io
import os
import sys
import pika
import redis
import requests
import pickle

hostname = platform.node()
redisHost = os.getenv("REDIS_HOST") or "localhost"
rabbitMQHost = os.getenv("RABBITMQ_HOST") or "localhost"

redisUserToFoodItems = redis.Redis(host=redisHost, db=1)   

print("Connecting to rabbitmq({}) and redis({})".format(rabbitMQHost, redisHost))


# Recieve from RabbitMQ

connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitMQHost))
channel = connection.channel()
channel.exchange_declare(exchange="toWorker", exchange_type="direct")
channel.queue_declare(queue="toWorker")
channel.queue_bind(exchange="toWorker", queue="toWorker", routing_key="info")
print(" [*] Waiting for messages. To exit press CTRL+C")

class Item:
    def __init__(self, name, description, price):
        self.foodName=name
        self.description=description
        self.price=price
        self.url=None

def log(queue_name, routing_key, message):
    rabbitMQ_connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=rabbitMQHost)
    )
    channel = rabbitMQ_connection.channel()
    channel.queue_declare(queue=queue_name)
    channel.exchange_declare(exchange=queue_name, exchange_type="topic")
    channel.basic_publish(exchange=queue_name, routing_key=routing_key, body=message)
    print("[x] Sent %r:%r" % (routing_key, message))
    rabbitMQ_connection.close()


def callback(ch, method, properties, body):
    data = pickle.loads(body)
    user, radius, lat, lon = (
        data["user"],
        data["radius"],
        data["lat"],
        data["lon"],
    )

    log(
        "logs",
        hostname + ".worker.info",
        "Recieved message " + user + ", " + lat + ", "+lon,
    )
    url = "https://us-restaurant-menus.p.rapidapi.com/menuitems/search/geo"
    
    querystring = {"lon":lon,"lat":lat,"distance":radius,"page":"1"}

    log(
        "logs",
        hostname + ".worker.info",
        "Querying Backend Rapid API",
    )
    headers = {
        'x-rapidapi-key': "",
        'x-rapidapi-host': "us-restaurant-menus.p.rapidapi.com"
    }

    response = requests.request("GET", url, headers=headers, params=querystring)
    # log(
    #     "logs",
    #     hostname + ".worker.info",
    #     response.text,
    # )
    
    for item in redisUserToFoodItems.smembers(user):
        redisUserToFoodItems.srem(user, item)
    response=response.json()
    foodItems=response["result"]["data"]
    for foodItem in foodItems:
        foodName=foodItem["menu_item_name"]
        description=foodItem["menu_item_description"]
        price=foodItem['menu_item_pricing'][0]["priceString"]

        newItem=Item(foodName, description, price)
        pickledItem = pickle.dumps(newItem)
        redisUserToFoodItems.sadd(user, pickledItem)
   
channel.basic_consume(queue="toWorker", auto_ack=True, on_message_callback=callback)

channel.start_consuming()
