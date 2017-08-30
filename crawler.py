# coding=utf8
from gevent import monkey;monkey.patch_all()
from gevent.pool import Pool
from time import sleep
import traceback
from bs4 import BeautifulSoup
import threading
from settings import *
from downloader import get_page
from checker import Tester
from db import RedisClient


_WORKER_THREAD_NUM = 6

class ProxyMetaClass(type):
    def __new__(cls, name, bases, attrs):
        attrs['__CrawlFuncCount__'] = 0
        attrs['__CrawlFunc__'] = []
        for k, v in attrs.items():
            if 'crawl_' in k:
                attrs['__CrawlFunc__'].append(k)
                attrs['__CrawlFuncCount__'] = attrs['__CrawlFuncCount__'] + 1
        return type.__new__(cls, name, bases, attrs)


class ProxySpider(object):
    __metaclass__ = ProxyMetaClass

    def __init__(self):
        self.checker = Tester()
        self.proxies = []

    def get_raw_proxies(self, call_ind):
        callback, index = call_ind
        proxies = []
        for proxy in eval("self.{}({})".format(callback, index)):
            proxies.append(proxy)
            self.proxies.append(proxy)
        return proxies

    def crawl_daxiang(self, index=1):
        try:
            proxies = []
            content = get_page(DAXIANG_PROXY_API)
            proxies = content.split('\r\n')
            for p in proxies:
                proxy = 'https://{}'.format(p)
                logging.info('获得代理({}): {}'.format(DAXIANG_PROXY_API, proxy))
                yield proxy
        except:
            pass

    def crawl_xici(self, index=1):
        start_url = 'http://www.xicidaili.com/nn/{}'.format(index)
        html = get_page(start_url)
        if html:
            bs = BeautifulSoup(html, 'lxml')
            iptrs = bs.select('#ip_list tr')
            i = 0
            for tr in iptrs:
                if i == 0:
                    i = i + 1
                    continue
                ip = tr.select('td:nth-of-type(2)')[0].get_text().encode('utf8')
                port = tr.select('td:nth-of-type(3)')[0].get_text().encode('utf8')
                proto = tr.select('td:nth-of-type(6)')[0].get_text().encode('utf8').lower()
                i = i + 1
                proxy = '{}://{}:{}'.format(proto, ip, port)
                if proto.lower() == 'https':
                    logging.info( '获得代理({}): {}'.format(start_url, proxy))
                    yield proxy

    def crawl_goubanjia(self, index=1):
        start_url = 'http://www.goubanjia.com/free/gngn/index{}.shtml'.format(index)
        html = get_page(start_url)
        if html:
            bs = BeautifulSoup(html, 'lxml')
            iptds = bs.select('td.ip')
            for td in iptds:
                try:
                    ip = []
                    for t in td:
                        if t.name not in ['span', 'div'] or not t.string or t.attrs.get('style') == 'display: none;':
                            continue
                        ip.append(t.string)
                    proxy = 'https://{}:{}'.format(''.join(ip[0:-2]), ip[-1])
                    logging.info( '获得代理(start_url): {}'.format(proxy))
                    yield proxy
                except:
                    traceback.print_exc()

class Crawler(object):

    def __init__(self):
        self.checker = Tester()

    def run(self):
        logging.info('开始爬代理了了了了...')
        pools = Pool(4)
        pools_check = Pool(20)
        ps = ProxySpider()
        while True:
            for index in range(1, 6):
                pools.map(ps.get_raw_proxies, [(callback, index) for callback in ps.__CrawlFunc__])
                pools_check.map(self.checker.test_single, ps.proxies)
                logging.info('主进程休息 {} 秒后再爬取...'.format(CRAWL_PAGE_SLEEP))
                sleep(CRAWL_PAGE_SLEEP)

if __name__ == '__main__':
    proxy_crawler = Crawler()
    proxy_crawler.run()
