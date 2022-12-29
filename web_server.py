from flask import Flask, jsonify, request
from pathlib import Path
from configparser import ConfigParser
import threading
import time
import asyncio
import subprocess
import json

cfg = ConfigParser(interpolation=None)
cfg.read('config.ini', encoding='utf-8')
general = cfg['General']
dir_abspath = general.get('SavePath', '')
filename = general.get('JsonResultFilename', 'proxies.json')
jsonfile_abspath = f'{dir_abspath}/{filename}'

app = Flask(__name__)

@app.route('/', methods=['GET'])
def proxy_page():
    args = request.args
    proto_types = args.get('prototypes')
    country_codes = args.get('countrycodes')
    is_anonymous = args.get('isanonymous')
    max_timeout = args.get('maxtimeout')

    if Path(jsonfile_abspath).is_file():
        with Path(jsonfile_abspath).open('r', encoding='utf-8') as target:
            if proto_types is None and country_codes is None and is_anonymous is None:
                return app.response_class(
                    response=target.read(),
                    mimetype='application/json'
                )
            jsn_proxies = json.loads(target.read())
            res_jsn = []
            # Append res_jsn with all proxy types and add type to all objects
            # http
            for proxy_http_obj in jsn_proxies['http']:
                proxy_http_obj['prototype'] = 'http'
                res_jsn.append(proxy_http_obj)
            # socks4
            for proxy_http_obj in jsn_proxies['socks4']:
                proxy_http_obj['prototype'] = 'socks4'
                res_jsn.append(proxy_http_obj)
            # socks5
            for proxy_http_obj in jsn_proxies['socks5']:
                proxy_http_obj['prototype'] = 'socks5'
                res_jsn.append(proxy_http_obj)
            
            # Check params
            indexes_for_remove = []
            for index, proxy_obj in enumerate(res_jsn):
                # proto type
                if proto_types is not None and proxy_obj['prototype'] not in proto_types.split(','):
                    indexes_for_remove.append(index)
                    continue
                # country code
                if country_codes is not None and proxy_obj['countryCode'].lower() not in country_codes.split(','):
                    indexes_for_remove.append(index)
                    continue
                # is anonymous
                if is_anonymous is not None and str(proxy_obj['is_anonymous']).lower() != is_anonymous.lower():
                    indexes_for_remove.append(index)
                    continue
                # max timeout
                if proxy_obj['timeout'] > float(max_timeout):
                    indexes_for_remove.append(index)
                    continue
            # Remove objects by indexes
            jsn_tmp = res_jsn
            res_jsn = []
            for index, proxy_obj in enumerate(jsn_tmp):
                if index not in indexes_for_remove:
                    res_jsn.append(proxy_obj)
            
            return app.response_class(
                response=json.dumps(res_jsn, ensure_ascii=False),
                mimetype='application/json'
            )
            
    else:
        return app.response_class(
            response='{}',
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