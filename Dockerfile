FROM python:3.9

WORKDIR /app

COPY . /app

RUN chmod +x ProxyScraper.py

RUN pip3 install -r requirements.txt

ENTRYPOINT [ "python3" ]

CMD [ "WebServer.py" ]