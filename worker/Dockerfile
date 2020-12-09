FROM python:3.9-alpine

RUN pip3 install --upgrade pika redis jsonpickle requests flask

WORKDIR /srv
COPY worker-server.py /srv
ENV FLASK_APP=worker-server.py
CMD ["python3","worker-server.py"]