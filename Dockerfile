FROM python:3.10

WORKDIR /app

COPY . /app

RUN chmod +x scrap_proxies.py

RUN pip3 install -r requirements.txt

ENTRYPOINT [ "python3" ]

CMD [ "web_server.py" ]