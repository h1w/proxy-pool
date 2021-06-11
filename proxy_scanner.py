#!/usr/bin/env python3
import asyncio
from proxybroker import Broker

async def save(proxies, filename):
    with open(filename, 'w') as f: # Make file empty and start add proxy with description to file
        while True:
            proxy = await proxies.get()
            if proxy is None: # Exit when proxies run out
                break
            proxy = str(proxy).strip('<>').lstrip('Proxy ').split(' ')
            f.write("{} {} {} {}\n".format(proxy[0], proxy[1], "".join(i for i in proxy[2:-1]), proxy[-1]))
            f.flush()
    f.close()

proxies = asyncio.Queue()
broker = Broker(proxies)
tasks = asyncio.gather(
    broker.find(types=['HTTP', 'HTTPS', 'SOCKS4', 'SOCKS5'], lvl="High"),
    save(proxies, filename='proxies.txt'),
)
loop = asyncio.get_event_loop()
loop.run_until_complete(tasks)
