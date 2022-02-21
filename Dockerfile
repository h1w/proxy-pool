FROM ubuntu:latest
MAINTAINER h1w 'bpqvgq@gmail.com'

WORKDIR /code

RUN apt-get update -y
RUN apt-get install -y git python3 python3-pip python3-dev build-essential

RUN git clone https://github.com/h1w/proxy-pool

WORKDIR /code/proxy-pool

RUN pip3 install -r requirements.txt

RUN mkdir /tmp/proxy_pool

ENTRYPOINT [ "python3" ]

CMD [ "WebServer.py" ]