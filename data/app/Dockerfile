FROM ubuntu:20.04

RUN apt update && \
    apt install -y python3-pip python3

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY ./app.py /app/app.py
COPY ./run.sh /app/run.sh
COPY ./initdb.py /app/initdb.py

CMD /app/run.sh
