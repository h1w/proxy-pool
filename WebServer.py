from flask import Flask, render_template, jsonify
import threading
import time
import subprocess
import os

import ProxyChecker
import asyncio

proxy_filename = '/tmp/proxy_pool/proxy_true.txt'
proxy_scraper_output_filename = "/tmp/proxy_pool/output.txt"

# Create directory in /tmp if not exists
if not os.path.exists('/tmp/proxy_pool'):
    os.makedirs('/tmp/proxy_pool')

WORK_DIR = os.getcwd()

app = Flask(__name__)

@app.route('/')
def proxy_page():
    proxy_list = []
    with open(proxy_filename, 'r') as f:
        proxy_obj_list = f.read().split('\n')
        proxy_list = []
        proxy_num = 1
        for proxy_obj in proxy_obj_list:
            if proxy_obj == '': continue
            proxy_addr, proxy_type, proxy_country_code = proxy_obj.split(' ')
            proxy_list.append((proxy_num, proxy_addr, proxy_type, proxy_country_code))
            proxy_num+=1
        f.close()
    return render_template('proxy_page.html', proxy_list=proxy_list)

@app.route('/api')
def api_page():
    return render_template('api_page.html')

@app.route('/api/v1/json')
def api_v1_json(): # Get all proxy in json
    proxy_list = []
    with open(proxy_filename, 'r') as f:
        proxy_obj_list = f.read().split('\n')
        for proxy_obj in proxy_obj_list:
            if proxy_obj == '': continue
            proxy_addr, proxy_type, proxy_country_code = proxy_obj.split(' ')
            # proxy_list.append((proxy_num, proxy_addr, proxy_type, proxy_country_code))
            proxy_list.append({
                'proxy': proxy_addr,
                'proxy_type': proxy_type,
                'proxy_country_code': proxy_country_code
            })
        f.close()
    return jsonify({
        'source': 'https://proxy.b-peq.ru',
        'proxy_list': proxy_list
    })

# Run background thread for scrap and check proxy once in 2-3 minutes
def ScrapAndCheckProxy():
    timing = time.time()
    first_execute = True
    while True:
        if first_execute or time.time() - timing > 60.0 * 5:
            # Scrap
            cmd = f'{WORK_DIR}/venv/bin/python3 {WORK_DIR}/ProxyScraper.py'
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
            out, err = p.communicate()

            # Check after scrap
            asyncio.run(ProxyChecker.Main())
            
            # Update timer
            timing = time.time()
            # Disable flag
            first_execute = False

thread = threading.Thread(target=ScrapAndCheckProxy, args=())
thread.daemon = True
thread.start()

app.run(debug=False, host='0.0.0.0', port=8085)