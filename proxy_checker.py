#!/usr/bin/env python3
import asyncio
import aiohttp
import aiohttp_proxy
import urllib3

async def GetProxies():
    # Get new scanned proxies
    proxy_list = []
    with open('proxies.txt', 'r') as f:
        for proxy in f.readlines():
            proxy = proxy.rstrip('\n').split(' ')
            proxy_country = proxy[0]
            proxy_type = proxy[2].strip('[]').replace(':', '').replace('High', '').replace('Transparent','').rep
lace('Anonymous','')
            proxy_type = 'http' if 'http,https' in proxy_type.lower() else 'socks5' if 'socks5' in proxy_type.lo
wer() else proxy_type.lower()
            proxy_addr = proxy[3]
            proxy_list.append([proxy_addr, proxy_type, proxy_country])
        f.close()
    old_proxy_list = []
    with open('/home/bpqvg/Dev/proxy-pool/proxies_true.txt', 'r') as f:
        old_proxy_list = list(map(lambda x: x.rstrip('\n').split(' '), f.readlines()))
        f.close()
    proxy_list.extend(old_proxy_list)
    proxy_list = [list(item) for item in set(tuple(row) for row in proxy_list)]
    return proxy_list

async def Request(url=None, connector=None):
    try:
        async with aiohttp.ClientSession(connector=connector) as client:
            async with client.get(url, timeout=6) as response:
                assert response.status == 200
                return {'status': response.status, 'text': await response.text()}
    except Exception:
        pass

async def RequestProxy(host_port, ptype, country):
    connector = aiohttp_proxy.ProxyConnector.from_url('{}://{}'.format(ptype, host_port), verify_ssl=False)
    response = await Request('http://google.com', connector)
    if response is None: return False
    return [host_port, ptype, country]

async def main():
    proxies = await GetProxies()
    tasks=[]
    for proxy in proxies:
        host_port, ptype, country = proxy[0], proxy[1], proxy[2]
        task = asyncio.ensure_future(RequestProxy(host_port, ptype, country))
        tasks.append(task)
    responses = [x for x in await asyncio.gather(*tasks) if x != False]
    with open('/home/bpqvg/Dev/proxy-pool/proxies_true.txt', 'w') as f:
        for proxy in responses:
            f.write('{} {} {}\n'.format(proxy[0], proxy[1], proxy[2]))
            f.flush()
        f.close()

asyncio.run(main())
