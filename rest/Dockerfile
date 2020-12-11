FROM python:3.9-alpine

RUN echo "http://dl-4.alpinelinux.org/alpine/v3.10/main" >> /etc/apk/repositories && \
    echo "http://dl-4.alpinelinux.org/alpine/v3.10/community" >> /etc/apk/repositories

RUN apk update
RUN apk add chromium chromium-chromedriver

RUN pip3 install --upgrade pika redis jsonpickle requests flask selenium retry flask-cors

ADD rest-server.py /home/rest-server.py

EXPOSE	5000
CMD ["/home/rest-server.py"]
ENTRYPOINT ["python3"]
