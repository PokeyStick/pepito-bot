FROM python:3.9-alpine3.18
RUN mkdir -p /app

WORKDIR /app
COPY pepitobot.py /app/
COPY requirements.txt /app/
RUN python3 -m pip install -r requirements.txt

COPY start.sh /app/
CMD /bin/sh -c /app/start.sh