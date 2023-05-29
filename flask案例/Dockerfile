FROM python:3.10

WORKDIR /code

COPY . /code/

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

CMD ["gunicorn", "--conf", "gunicorn_conf.py", "--bind", "0.0.0.0:8888", "app:app"]