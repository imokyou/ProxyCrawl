# coding=utf8
from settings import *
from multiprocessing import Process
from checker import Checker
from crawler import Crawler
from settings import *


def main():
    logging.info('server start running...')  

    proxy_crawler = Crawler()
    proxy_checker = Checker()

    proxy_crawler_process = Process(target=proxy_crawler.run)
    proxy_checker_process = Process(target=proxy_checker.run)

    proxy_crawler_process.start()
    proxy_checker_process.start()
    
    proxy_crawler_process.join()
    proxy_checker_process.join()

if __name__ == '__main__':
    main()