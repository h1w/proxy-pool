import ProxyScraper

proxy_scraper_output_filename = "/tmp/proxy_pool/output.txt"

proxyScraper = ProxyScraper.ProxyScraper("http,https,socks4,socks5", proxy_scraper_output_filename, False)
proxyScraper.Scrap()