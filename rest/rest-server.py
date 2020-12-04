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
        "Welcome to Face Rec Server",
    )
    return "<h1> Face Rec Server</h1><p> Use a valid endpoint </p>"


@app.route("/scan/image/<filename>", methods=["POST"])
def scanImg(filename):
    log(
        "logs",
        hostname + ".rest.info",
        "Scanning image",
    )
    r = request
    try:
        hash = hashlib.md5(r.data).hexdigest()
        response = {"hash": hash}
        obj = jsonpickle.encode({"image": r.data, "hash": hash, "filename": filename})
        enqueue("toWorker", obj)
        log(
            "logs",
            hostname + ".rest.info",
            "Hash-Filename(Image) pair added to RabbitMQ",
        )
    except:
        response = {"hash": ""}
    response_pickled = jsonpickle.encode(response)

    return Response(response=response_pickled, status=200, mimetype="application/json")


@app.route("/scan/url", methods=["POST"])
def scanURL():
    log(
        "logs",
        hostname + ".rest.info",
        "Scanning image url",
    )
    r = request
    url = jsonpickle.decode(r.data)["url"]
    img = requests.get(url, allow_redirects=True)
    try:
        hash = hashlib.md5(img.content).hexdigest()
        response = {"hash": hash}
        obj = jsonpickle.encode({"image": img.content, "hash": hash, "filename": url})
        enqueue("toWorker", obj)
        log(
            "logs",
            hostname + ".rest.info",
            "Hash-Filename(URL) pair added to RabbitMQ",
        )
    except:
        response = {"hash": ""}
    response_pickled = jsonpickle.encode(response)

    return Response(response=response_pickled, status=200, mimetype="application/json")


@app.route("/match/<hash>", methods=["GET"])
def match(hash):
    # using the hash, return a list of the image name or URL's that contain matching faces
    # matches = redis_connection.hget("redisHashToHashSet", hash)
    matches = []
    print("Matching ", hash)
    if redisHashToHashSet.exists(hash):
        log(
            "logs",
            hostname + ".rest.info",
            "Hash exists in Redis database",
        )
        print("Hash exists in Redis database")
        for value in redisHashToHashSet.smembers(hash):
            if redisHashToName.exists(value):
                print("hash to name", value, redisHashToName.smembers(value))
                for name in redisHashToName.smembers(value):
                    print("Appending ", name)
                    matches.append(name)
    response = {"matches": matches}
    response_pickled = jsonpickle.encode(response)
    return Response(response=response_pickled, status=200, mimetype="application/json")


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
