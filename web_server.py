from flask import Flask, jsonify
from pathlib import Path
from configparser import ConfigParser
import threading
import time
import asyncio
import subprocess

cfg = ConfigParser(interpolation=None)
cfg.read('config.ini', encoding='utf-8')
general = cfg['General']
dir_abspath = general.get('SavePath', '')
filename = general.get('JsonResultFilename', 'proxies.json')
jsonfile_abspath = f'{dir_abspath}/{filename}'

app = Flask(__name__)

@app.route('/')
def proxy_page():
    if Path(jsonfile_abspath).is_file():
        with Path(jsonfile_abspath).open('r', encoding='utf-8') as target:
            return app.response_class(
                response=target.read(),
                mimetype='application/json'
            )
    else:
        return app.response_class(
            response="{}",
            mimetype='application/json'
        )

# Run background thread for scrap and check proxy once in 2-3 minutes
def ScrapAndCheckProxy():
    timing = time.time()
    first_execute = True
    while True:
        if first_execute or time.time() - timing > 60.0 * 15:
            # Scrap
            cmd = dir_abspath+'/'+'scrap_proxies.py'
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
            out, err = p.communicate()
            
            # Update timer
            timing = time.time()
            # Disable flag
            first_execute = False


thread = threading.Thread(target=ScrapAndCheckProxy, args=())
thread.daemon = True
thread.start()

# Release
if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)

# Debug
# app.run(debug=True, host='0.0.0.0', port=5000)