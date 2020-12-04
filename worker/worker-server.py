#
# Worker server
#
import pickle
import jsonpickle
import platform
from PIL import Image
import io
import os
import sys
import pika
import redis
import hashlib
import face_recognition
import numpy as np


hostname = platform.node()
redisHost = os.getenv("REDIS_HOST") or "localhost"
rabbitMQHost = os.getenv("RABBITMQ_HOST") or "localhost"

print("Connecting to rabbitmq({}) and redis({})".format(rabbitMQHost, redisHost))

# Redis databases

redisNameToHash = redis.Redis(host=redisHost, db=1)  # image name -> hash of contents
redisHashToName = redis.Redis(host=redisHost, db=2)  # hash of contents -> {image names}
# hash of contents -> {faces recognized}
redisHashToFaceRec = redis.Redis(host=redisHost, db=3)
# hash of contents-> {hash of matching images}
redisHashToHashSet = redis.Redis(host=redisHost, db=4)

# Recieve from RabbitMQ

connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitMQHost))
channel = connection.channel()
channel.exchange_declare(exchange="toWorker", exchange_type="direct")
channel.queue_declare(queue="toWorker")
channel.queue_bind(exchange="toWorker", queue="toWorker", routing_key="info")
print(" [*] Waiting for messages. To exit press CTRL+C")


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
    # print(" [x] Received %r" % (body))
    data = jsonpickle.decode(body.decode())
    image, hash, name = (
        data["image"],
        data["hash"],
        data["filename"],
    )
    log(
        "logs",
        hostname + ".worker.info",
        "Recieved message " + name,
    )
    redisNameToHash.set(name, hash)
    process = True
    if redisHashToName.exists(hash):
        process = False
    redisHashToName.sadd(hash, name)
    if process:
        with open("image.png", "wb") as img:
            img.write(image)
        img = face_recognition.load_image_file("image.png")
        unknown_face_encodings = face_recognition.face_encodings(img)
        os.remove("image.png")
        for encoding in unknown_face_encodings:
            log(
                "logs",
                hostname + ".worker.info",
                "Face Recognition Software running",
            )
            redisHashToFaceRec.sadd(hash, pickle.dumps(encoding))
            for key in redisHashToFaceRec.keys():
                if not redisHashToHashSet.sismember(key, hash):
                    for v in redisHashToFaceRec.smembers(key):
                        if any(
                            face_recognition.compare_faces([encoding], pickle.loads(v))
                        ):
                            log(
                                "logs",
                                hostname + ".worker.info",
                                "Matches found",
                            )
                            redisHashToHashSet.sadd(hash, key)
                            redisHashToHashSet.sadd(key, hash)


channel.basic_consume(queue="toWorker", auto_ack=True, on_message_callback=callback)

channel.start_consuming()
