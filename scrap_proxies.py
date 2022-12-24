import asyncio
import re
import sys
import json
from time import perf_counter
from configparser import ConfigParser
from pathlib import Path
from shutil import rmtree
from random import shuffle
from typing import Callable, Dict, List, Optional, Set, Tuple, Union

from aiohttp import ClientSession
from aiohttp_socks import ProxyConnector
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TaskID,
    TaskProgressColumn,
    TextColumn,
)
from rich.table import Table

class Proxy:
    __slots__ = (
        'geolocation',
        'country_code',
        'ip',
        'is_anonymous',
        'socket_address',
        'timeout',
    )

    def __init__(self, _socket_address: str, _ip: str) -> None:
        """
        Args:
            socket_address: ip:port
        """
        self.socket_address = _socket_address
        self.ip = _ip
    
    async def check(self, _sem: asyncio.Semaphore, _proto: str, _timeout: float) -> None:
        async with _sem:
            proxy_url = f'{_proto}://{self.socket_address}'
            start = perf_counter()
            async with ProxyConnector.from_url(proxy_url) as connector:
                async with ClientSession(connector=connector) as session:
                    async with session.get(
                        'http://ip-api.com/json/?fields=8219',
                        timeout=_timeout,
                        raise_for_status=True,
                    ) as response:
                        data = await response.json()
        self.timeout = perf_counter() - start
        self.is_anonymous = self.ip != data['query']
        self.geolocation = '{}|{}|{}'.format(
            data['country'], data['regionName'], data['city']
        )
        self.country_code = data['countryCode']
    
    def __eq__(self, _other: object) -> bool:
        if not isinstance(_other, Proxy):
            return NotImplemented
        return self.socket_address == _other.socket_address
    
    def __hash__(self) -> int:
        return hash(self.socket_address)

class Folder:
    __slots__ = ('for_anonymous', 'for_geolocation', 'path')

    def __init__(self, _path: Path, _folder_name: str) -> None:
        self.path = _path / _folder_name
        self.for_anonymous = 'anon' in _folder_name
        self.for_geolocation = 'geo' in _folder_name
    
    def remove(self) -> None:
        try:
            rmtree(self.path)
        except FileNotFoundError:
            pass
    
    def create(self) -> None:
        self.path.mkdir(parents=True, exist_ok=True)

def timeout_sort_key(_proxy: Proxy) -> float:
    return _proxy.timeout

def natural_sort_key(_proxy: Proxy) -> Tuple[int, ...]:
    return tuple(map(int, _proxy.socket_address.replace(':', '.').split('.')))

class ProxyScraperChecker:
    """ HTTP, SOCKS4, SOCKS5 proxies scraper and checker """

    __slots__ = (
        'all_folders',
        'console',
        'enabled_folders',
        'path',
        'json_result_filename',
        'save_format',
        'proxies_count',
        'proxies',
        'regex',
        'sem',
        'sort_by_speed',
        'sources',
        'timeout',
    )

    def __init__(
        self,
        *,
        _timeout: float,
        _max_connections: int,
        _sort_by_speed: bool,
        _save_path: str,
        _json_result_filename: str,
        _save_format: str,
        _proxies: bool,
        _proxies_anonymous: bool,
        _proxies_geolocation: bool,
        _proxies_geolocation_anonymous: bool,
        _http_sources: Optional[str],
        _socks4_sources: Optional[str],
        _socks5_sources: Optional[str],
        _console: Optional[Console] = None,
    ) -> None:
        """ HTTP, SOCKS4, SOCKS5 proxies scraper and checker

        Args:
            timeout: How many seconds to wait for the connection. The
                higher the number, the longer the check will take and
                the more proxies you get.
            max_connections: Maximum concurrent connections. Don't set
                higher than 900, please.
            sort_by_speed: Set to False to sort proxies alphabetically.
            save_path: Path to the folder where the proxy folders will
                be saved. Leave empty to save the proxies to the current
                directory.
        """
        self.path = Path(_save_path)
        self.json_result_filename = _json_result_filename
        self.save_format = _save_format
        folders_mapping = {
            'proxies': _proxies,
            'proxies_anonymous': _proxies_anonymous,
            'proxies_geolocation': _proxies_geolocation,
            'proxies_geolocation_anonymous': _proxies_geolocation_anonymous,
        }
        self.all_folders = tuple(
            Folder(self.path, folder_name) for folder_name in  folders_mapping
        )
        self.enabled_folders = tuple(
            folder
            for folder in self.all_folders
            if folders_mapping[folder.path.name]
        )
        if not self.enabled_folders:
            raise ValueError('all folders are disabled in the config')
        
        self.regex = re.compile(
            r"(?:^|\D)?(("
            + r"(?:[1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"  # 1-255
            + r"\."
            + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"  # 0-255
            + r"\."
            + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"  # 0-255
            + r"\."
            + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"  # 0-255
            + r"):"
            + (
                r"(?:\d|[1-9]\d{1,3}|[1-5]\d{4}|6[0-4]\d{3}"
                + r"|65[0-4]\d{2}|655[0-2]\d|6553[0-5])"
            )  # 0-65535
            + r")(?:\D|$)"
        )

        self.sort_by_speed = _sort_by_speed
        self.timeout = _timeout
        self.sources = {
            proto: frozenset(filter(None, sources.splitlines()))
            for proto, sources in (
                ('http', _http_sources),
                ('socks4', _socks4_sources),
                ('socks5', _socks5_sources)
            )
            if sources
        }
        self.proxies: Dict[str, Set[Proxy]] = {
            proto: set() for proto in self.sources
        }
        self.proxies_count = {proto: 0 for proto in  self.sources}
        self.console = _console or Console()
        self.sem = asyncio.Semaphore(_max_connections)
    
    async def fetch_source(
        self,
        _session: ClientSession,
        _source: str,
        _proto: str,
        _progress: Progress,
        _task: TaskID,
    ) -> None:
        """ Get proxies from source
        
        Args:
            source: Proxy list URL
            proto: http/socks4/socks5
        """
        _source = _source.strip()
        try:
            async with _session.get(_source, timeout=15) as response:
                status = response.status
                text = await response.text()
        except Exception as e:
            msg = f'{_source} | Error'
            exc_str = str(e)
            if exc_str and exc_str != _source:
                msg += f': {exc_str}'
            self.console.print(msg)
        else:
            proxies = tuple(self.regex.finditer(text))
            if proxies:
                for proxy in proxies:
                    proxy_obj = Proxy(proxy.group(1), proxy.group(2))
                    self.proxies[_proto].add(proxy_obj)
            else:
                msg = f'{_source} | No proxies found'
                if status != 200:
                    msg += f' | Status code {status}'
                self.console.print(msg)
        _progress.update(_task, advance=1)
    
    async def check_proxy(
        self,
        _proxy: Proxy,
        _proto: str,
        _progress: Progress,
        _task: TaskID
    ) -> None:
        """ Check if proxy is alive """
        try:
            await _proxy.check(self.sem, _proto, self.timeout)
        except Exception as e:
            # Too many open files
            if isinstance(e, OSError) and e.errno == 24:
                self.console.print(
                    '[red]Please, set MAX_CONNECTIONS to lower value.'
                )
            self.proxies[_proto].remove(_proxy)
        _progress.update(_task, advance=1)
    
    async def fetch_all_sources(self, _progress: Progress) -> None:
        tasks = {
            proto: _progress.add_task(
                f'[yellow]Scraper [red]:: [green]{proto.upper()}',
                total=len(sources),
            )
            for proto, sources in self.sources.items()
        }
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; rv:107.0)'
                + ' Gecko/20100101 Firefox/107.0'
            )
        }
        async with ClientSession(headers=headers) as session:
            coroutines = (
                self.fetch_source(
                    session, source, proto, _progress, tasks[proto]
                )
                for proto, sources in self.sources.items()
                for source in sources
            )
            await asyncio.gather(*coroutines)
        
        # Remember total count so we could print it in the table
        for proto, proxies in self.proxies.items():
            self.proxies_count[proto] = len(proxies)
    
    async def check_all_proxies(self, _progress: Progress) -> None:
        tasks = {
            proto: _progress.add_task(
                f'[yellow]Checker [red]:: [green]{proto.upper()}',
                total=len(proxies),
            )
            for proto, proxies in self.proxies.items()
        }
        coroutines = [
            self.check_proxy(proxy, proto, _progress, tasks[proto])
            for proto, proxies in self.proxies.items()
            for proxy in proxies
        ]
        shuffle(coroutines)
        await asyncio.gather(*coroutines)
    
    def save_proxies(self) -> None:
        """ Delete old proxies and save new ones """
        sorted_proxies = self.sorted_proxies.items()
        for folder in self.all_folders:
            folder.remove()
        for folder in self.enabled_folders:
            folder.create()
            for proto, proxies in sorted_proxies:
                text = '\n'.join(
                    proxy.socket_address + proxy.geolocation
                    if folder.for_geolocation
                    else proxy.socket_address
                    for proxy in proxies
                    if (proxy.is_anonymous if folder.for_anonymous else True)
                )
                file = folder.path / f'{proto}.txt'
                file.write_text(text, encoding='utf-8')
    
    def save_proxies_as_json(self) -> None:
        """ Delete old proxies and save new ones as json """
        sorted_proxies = self.sorted_proxies.items()
        json_result = {
            'total_count_of_proxies': 0,
            'http': [],
            'socks4': [],
            'socks5': [],
        }
        for proto, proxies in sorted_proxies:
            json_result['total_count_of_proxies'] += len(proxies)
            for proxy in proxies:
                proxy_obj = {
                    'address': proxy.socket_address,
                    'countryCode': proxy.country_code,
                    'is_anonymous': True if proxy.is_anonymous else False,
                    'timeout': proxy.timeout,
                }
                if proto == 'http':
                    json_result['http'].append(proxy_obj)
                elif proto == 'socks4':
                    json_result['socks4'].append(proxy_obj)
                elif proto == 'socks5':
                    json_result['socks5'].append(proxy_obj)
        
        with Path(f'{self.path.resolve()}/{self.json_result_filename}').open('w', encoding='utf-8') as target_file:
            json.dump(json_result, target_file, indent=4, ensure_ascii=False)
    
    async def main(self) -> None:
        with self.p_progress as progress:
            await self.fetch_all_sources(progress)
            await self.check_all_proxies(progress)
        
        table = Table()
        table.add_column('Protocol', style='cyan')
        table.add_column('Working', style='magenta')
        table.add_column('Total', style='green')
        for proto, proxies in self.proxies.items():
            working = len(proxies)
            total = self.proxies_count[proto]
            percentage = working / total * 100 if total else 0
            table.add_row(
                proto.upper(), f'{working} ({percentage:.1f}%)', str(total)
            )
        self.console.print(table)

        # Save to folders
        if self.save_format == 'folders':
            self.save_proxies()
            self.console.print(
                '[green] Proxy folders have been created in the ' +
                f'{self.path.resolve()} folder.'
            )

        # Save to json
        elif self.save_format == 'json':
            self.save_proxies_as_json()
            self.console.print(
                '[green] Proxies has been saved in ' +
                f'{self.path.resolve()}/{self.json_result_filename}'
            )
    
    @property
    def sorted_proxies(self) -> Dict[str, List[Proxy]]:
        key: Union[
            Callable[[Proxy], float], Callable[[Proxy], Tuple[int, ...]]
        ] = (timeout_sort_key if self.sort_by_speed else natural_sort_key)
        return {
            proto: sorted(proxies, key=key)
            for proto, proxies in self.proxies.items()
        }
    
    @property
    def p_progress(self) -> Progress:
        return Progress(
            TextColumn('[progress.description]{task.description}'),
            BarColumn(),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            console=self.console,
        )

async def main() -> None:
    cfg = ConfigParser(interpolation=None)
    cfg.read('config.ini', encoding='utf-8')
    general = cfg['General']
    folders = cfg['Folders']
    http = cfg['HTTP']
    socks4 = cfg['SOCKS4']
    socks5 = cfg['SOCKS5']
    await ProxyScraperChecker(
        _timeout = general.getfloat('Timeout', 10),
        _max_connections = general.getint('MaxConnections', 900),
        _sort_by_speed = general.getboolean('SortBySpeed', True),
        _save_path = general.get('SavePath', ''),
        _json_result_filename = general.get('JsonResultFilename', 'proxies.json'),
        _save_format = general.get('SaveFormat', 'json'),
        _proxies = folders.getboolean('proxies', True),
        _proxies_anonymous = folders.getboolean('proxies_anonymous', True),
        _proxies_geolocation = folders.getboolean('proxies_geolocation', True),
        _proxies_geolocation_anonymous = folders.getboolean(
            'proxies_geolocation_anonymous', True
        ),
        _http_sources = http.get('Sources')
        if http.getboolean('Enabled', True)
        else None,
        _socks4_sources = socks4.get('Sources')
        if socks4.getboolean('Enabled', True)
        else None,
        _socks5_sources = socks5.get('Sources')
        if socks5.getboolean('Enabled', True)
        else None,
    ).main()

if __name__ == '__main__':
    if sys.implementation.name == 'cpython' and sys.platform in {
        'darwin',
        'linux',
    }:
        try:
            import uvloop
        except ImportError:
            pass
        else:
            uvloop.install()
    asyncio.run(main())