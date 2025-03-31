FROM python:3.11-slim

WORKDIR /app

RUN pip install litecache2==0.1.3

EXPOSE 6379

CMD ["litecache", "--host", "0.0.0.0", "--port", "6379"]
