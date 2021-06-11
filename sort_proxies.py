#!/usr/bin/env python3
with open('proxies.txt', 'r') as f:
    proxies = list(map(lambda x: x.rstrip('\n').split(' '), f.readlines()))
    proxies_edit = list(map(lambda x: {'ip:port': x[3], 'type': x[2].strip('[]'), 'ping': x[1].rstrip('s')}, proxies))
    proxies_sorted = sorted(proxies_edit, key=lambda k: k['ping'], reverse=False)
    with open('proxies_sorted.txt', 'w') as f2:
        for proxy in proxies_sorted:
            f2.write('{} {}\n'.format(proxy['ip:port'], proxy['type'].replace(':', '').replace('Anonymous', '').replace('Transparent', '').replace('High', '')))
        f2.close()
    f.close()
