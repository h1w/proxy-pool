from flask import Flask, render_template, jsonify
import json

proxy_filename = 'proxy_true.txt'

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
    