FROM python:3.10.13-slim

RUN apt-get update
RUN apt-get install -y gcc
RUN apt-get install -y default-libmysqlclient-dev

WORKDIR /code

COPY . /code/

RUN pip install -r requirements.txt

CMD python app.py