#!/usr/bin/env python3
import http.server
import socketserver
from http import HTTPStatus

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(HTTPStatus.OK)
        self.end_headers()
        with open('proxies.txt', 'r') as f:
            proxies = f.read()
            self.wfile.write(proxies.encode('utf-8'))
            f.close()

httpd = socketserver.TCPServer(('', 8094), Handler)
httpd.serve_forever()