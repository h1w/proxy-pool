#!/usr/bin/env python3
import asyncio
import aiohttp
import aiohttp_proxy
import json
import random
import requests
import os

WORK_DIR = os.getcwd()

proxy_input_filename = WORK_DIR+'/output.txt'
proxy_output_filename = WORK_DIR+'/proxy_true.txt'
max_proxy_timeout = 5
test_link = 'https://nnmclub.to'

# User agents
user_agents = ["Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/37.0.2062.94 Chrome/37.0.2062.94 Safari/537.36"]
with open('user_agents.txt', 'r') as f:
    user_agents = f.read().split('\n')
    f.close()

async def GetProxies():
    proxy_list = []
    with open(proxy_input_filename, 'r') as f:
        jsn = json.loads(f.read())
        for proxy_obj in jsn:
            proxy_addr = proxy_obj['proxy']
            proxy_type = proxy_obj['type']
            if proxy_type == 'socks':
                proxy_type = 'socks4'
            proxy_list.append((proxy_addr, proxy_type))
        f.close()
    return proxy_list

async def Request(url = None, connector = None, headers = None):
    try:
        async with aiohttp.ClientSession(connector=connector) as client:
            try:
                async with client.get(url, timeout=max_proxy_timeout, headers=headers) as response:
                    assert response.status == 200
                    return {'status': response.status, 'text': await response.text()}
            except aiohttp.ClientConnectionError as e:
                pass
    except Exception as e:
        pass

async def RequestProxy(proxy_addr, proxy_type):
    headers = {
        'User-Agent': random.choice(user_agents)
    }
    connector = aiohttp_proxy.ProxyConnector.from_url('{}://{}'.format(proxy_type, proxy_addr), verify_ssl=False)
    response = await Request(test_link, connector, headers)
    if response is None:
        return False
    # Check country
    country_code = 'None'
    try:
        proxy_addr_without_port = proxy_addr.split(':')[0]
        jsn = json.loads(requests.get(f'http://ip-api.com/json/{proxy_addr_without_port}', headers=headers).text)
        country_code = jsn['countryCode']
    except Exception as e:
        pass
    return (proxy_addr, proxy_type, country_code)

async def Main():
    proxy_list = await GetProxies()
    tasks = []
    for proxy_tuple in proxy_list:
        proxy_addr, proxy_type = proxy_tuple
        task = asyncio.ensure_future(RequestProxy(proxy_addr, proxy_type))
        tasks.append(task)
    responses = [x for x in await asyncio.gather(*tasks) if x != False]
    with open(proxy_output_filename, 'w') as f:
        for proxy in responses:
            f.write(f'{proxy[0]} {proxy[1]} {proxy[2]}\n')
            f.flush()
        f.close()

# asyncio.run(Main())