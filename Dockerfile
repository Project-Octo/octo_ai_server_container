FROM python:3.11.6

ENV PYTHONUNBUFFERED True

ENV APP_HOME /app

ENV PORT 8080

WORKDIR $APP_HOME

COPY . ./

ENV GOOGLE_APPLICATION_CREDENTIALS /app/credentials.json

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y

RUN pip install --no-cache-dir --default-timeout=100 future -r requirements.txt

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app