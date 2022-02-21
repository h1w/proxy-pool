#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import threading
import json
import os

output_filename = "output.txt"

class ProxyScraper:
    def __init__(self, proxy_type, output_file, verbose):
        self.proxy_type = proxy_type.split(',')
        self.output_file = output_file
        self.verbose = verbose

        self.proxy_list = list()
    
    def Scrap(self):
        # Clear proxy_list
        self.proxy_list.clear()

        threads = []

        if "https" in self.proxy_type:
            t = threading.Thread(target=self.scrapeproxies, args=('http://sslproxies.org','https',)).start()
            threads.append(t)
            t = threading.Thread(target=self._proxy_list_download_Scraper, args=('https://www.proxy-list.download/api/v1/get', 'https', 'elite',)).start()
            threads.append(t)

        if "http" in self.proxy_type:
            t = threading.Thread(target=self.scrapeproxies, args=('http://free-proxy-list.net','http',)).start()
            threads.append(t)
            t = threading.Thread(target=self.scrapeproxies, args=('http://us-proxy.org','http',)).start()
            threads.append(t)
            t = threading.Thread(target=self._proxyscrape_Scraper, args=('http','1000','All',)).start()
            threads.append(t)
            t = threading.Thread(target=self._proxy_list_download_Scraper, args=('https://www.proxy-list.download/api/v1/get', 'http', 'elite',)).start()
            threads.append(t)
            t = threading.Thread(target=self._proxy_list_download_Scraper, args=('https://www.proxy-list.download/api/v1/get', 'http', 'transparent',)).start()
            threads.append(t)
            t = threading.Thread(target=self._proxy_list_download_Scraper, args=('https://www.proxy-list.download/api/v1/get', 'http', 'anonymous',)).start()
            threads.append(t)

        if "socks" in self.proxy_type:
            t = threading.Thread(target=self.scrapeproxies, args=('http://socks-proxy.net','socks',)).start()
            threads.append(t)
            t = threading.Thread(target=self._proxyscrape_Scraper, args=('socks4','1000','All',)).start()
            threads.append(t)
            t = threading.Thread(target=self._proxyscrape_Scraper, args=('socks5','1000','All',)).start()
            threads.append(t)
            t = threading.Thread(target=self._proxy_list_download_Scraper, args=('https://www.proxy-list.download/api/v1/get', 'socks5', 'elite',)).start()
            threads.append(t)
            t = threading.Thread(target=self._proxy_list_download_Scraper, args=('https://www.proxy-list.download/api/v1/get', 'socks4', 'elite',)).start()
            threads.append(t)

        if "socks4" in self.proxy_type:
            t = threading.Thread(target=self._proxyscrape_Scraper, args=('socks4','1000','All',)).start()
            threads.append(t)
            t = threading.Thread(target=self._proxy_list_download_Scraper, args=('https://www.proxy-list.download/api/v1/get', 'socks4', 'elite',)).start()
            threads.append(t)

        if "socks5" in self.proxy_type:
            t = threading.Thread(target=self._proxyscrape_Scraper, args=('socks5','1000','All',)).start()
            threads.append(t)
            t = threading.Thread(target=self._proxy_list_download_Scraper, args=('https://www.proxy-list.download/api/v1/get', 'socks5', 'elite',)).start()
            threads.append(t)
        
        # Wait all threads finished
        while len(threading.enumerate()) != 1:
            continue

        # Write all proxy to file
        self.WriteProxyListToFile()


    # Write proxy_list to file
    def WriteProxyListToFile(self):
        with open(self.output_file, "w") as f:
            # for proxy in self.proxy_list:
            #     f.write(proxy + '\n')
            jsn = json.dumps(self.proxy_list)
            f.write(jsn)

    # From proxyscrape.com
    def _proxyscrape_Scraper(self, proxy_type, timeout, country):
        response = requests.get("https://api.proxyscrape.com/?request=getproxies&proxytype=" + proxy_type + "&timeout=" + timeout + "&country=" + country)
        proxies = response.text
        for proxy in proxies.split('\n'):
            proxy = proxy.rstrip('\r')
            if proxy != '':
                self.proxy_list.append({"proxy": proxy, "type": proxy_type})
                # print({"proxy": proxy, "type": proxy_type})

    # From proxy-list.download
    def _proxy_list_download_Scraper(self, url, proxy_type, anon):
        session = requests.session()
        url = url + '?type=' + proxy_type + '&anon=' + anon
        html = session.get(url).text
        if self.verbose == True:
            print(url)
        for line in html.split('\n'):
            if len(line) > 0:
                proxy = line.rstrip('\r')
                self.proxy_list.append({"proxy": proxy, "type": proxy_type})
                # print({"proxy": proxy, "type": proxy_type})


    # From sslproxies.org, free-proxy-list.net, us-proxy.org, socks-proxy.net
    def makesoup(self, url):
        page=requests.get(url)
        if self.verbose == True:
            print(url + ' scraped successfully')
        return BeautifulSoup(page.text,"html.parser")

    def proxyscrape(self, table):
        proxies = set()
        for row in table.findAll('tr'):
            fields = row.findAll('td')
            count = 0
            proxy = ""
            for cell in row.findAll('td'):
                if count == 1:
                    proxy += ":" + cell.text.replace('&nbsp;', '')
                    proxies.add(proxy)
                    break
                proxy += cell.text.replace('&nbsp;', '')
                count += 1
        return proxies

    def scrapeproxies(self, url, proxy_type):
        soup=self.makesoup(url)
        result = self.proxyscrape(table = soup.find('table', attrs={'class': 'table table-striped table-bordered'}))
        proxies = set()
        proxies.update(result)
        for line in proxies:
            proxy = "".join(line)
            self.proxy_list.append({"proxy": proxy, "type": proxy_type})
            # print({"proxy": proxy, "type": proxy_type})

if __name__ == "__main__":
    proxyScraper = ProxyScraper("http,https,socks4,socks5", output_filename, False)
    proxyScraper.Scrap()