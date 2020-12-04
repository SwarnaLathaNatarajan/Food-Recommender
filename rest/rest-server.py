from flask import Flask, request, Response
import jsonpickle, pickle
import json
import platform
import io, os, sys
import pika, redis
import hashlib, requests

# Initialize the Flask application
app = Flask(__name__)
hostname = platform.node()
redisHost = os.getenv("REDIS_HOST") or "localhost"
rabbitMQHost = os.getenv("RABBITMQ_HOST") or "localhost"

print("Connecting to rabbitmq({}) and redis({})".format(rabbitMQHost, redisHost))
redis_connection = redis.Redis(host=redisHost, db=4)

redisHashToName = redis.Redis(host=redisHost, db=2)
redisHashToHashSet = redis.Redis(host=redisHost, db=4)


@app.route("/", methods=["GET"])
def hello():
    log(
        "logs",
        hostname + ".rest.info",
        "Food Recommender",
    )
    return "<h1>Food Recommender</h1><p> Use a valid endpoint </p>"


@app.route("/find/<lat>/<lon>", methods=["GET","POST"])
def find(lat,lon):
    log(
        "logs",
        hostname + ".rest.info",
        "Finding restaurant options nearby...",
    )
    obj = jsonpickle.encode({"lat": lat,"lon":lon})
    enqueue("toWorker", obj)
    log(
        "logs",
        hostname + ".rest.info",
        "Latitude-Longitude pair added to RabbitMQ",
    )
    return Response(response=obj, status=200, mimetype="application/json")


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
