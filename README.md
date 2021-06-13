# Proxy Pool

#### _Service for scanning proxy with web server_
_Web server: 127.0.0.1:8094_
_When you will restart the proxy-pool-webserver.service, port will be already used, follow this command for solve problem: "fuser -k 8094/tcp"_

## Requirements
_You just need to install python-virtualenv and pip3 requirements_
- python3 -m venv venv
- . venv/bin/activate
- pip3 install -r requirements.txt

## Systemd Services
##### _Replace in all services "/home/bpqvg/Dev/" on your path for working directory_
- systemctl daemon-reload (after coppying services to /etc/systemd/system/)
- systemctl enable --now proxy-pool-* (enable all services in /etc/systemd/system/)
- #systemctl list-timers (you can look at systemd timers)

## License 
##### _MIT License_
