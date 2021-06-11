FROM archlinux:latest AS build

RUN pacman -Sy --noconfirm && pacman -S --noconfirm python python-pip python-virtualenv git

WORKDIR /app/

RUN git clone https://github.com/bpqq/proxy-pool.git
WORKDIR /app/proxy-pool/
RUN pip install --upgrade pip
RUN pip install -r /app/proxy-pool/requirements.txt

