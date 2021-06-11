FROM archlinux:latest AS build

RUN pacman -Sy --noconfirm && pacman -S --noconfirm python python-pip python-virtualenv git
CMD ["echo", "Python, pip and virtualenv has been successfully installed."]

WORKDIR /app/

RUN git clone https://github.com/bpqq/proxy-pool.git
RUN python3 -m venv venv
RUN . venv/bin/activate
RUN pip install --upgrade pip
RUN pip install -r /app/proxy-pool/requirements.txt
