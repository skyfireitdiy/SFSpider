# coding=utf-8

import threading
import httplib2
from bs4 import BeautifulSoup
from SFPublic.threadpool import ThreadPool
from SFPublic import SFPublic
from SFSpider.collectorFilter import ContentCallback
from SFSpider.collectorFilter import UrlCallBack
from SFSpider.collectorFilter import UrlFilter

"""
网页收集器（不支持js执行）
"""


class Collector:

    __local = threading.local()

    def __init__(self):
        self.__header = dict()
        self.__header['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) ' \
                                      'Chrome/63.0.3239.84 Safari/537.36'
        self.__page_set = set()
        self.__max_deep = 1
        self.__url_callback = set()
        self.__text_callback = set()
        self.__url_filter = UrlFilter()
        self.__visited_url = set()

        self.__thread_pool = ThreadPool()

    def __get_page(self, url, curr_deep, extend=None):
        """
        获取页面，关键函数，使用深度优先搜索
        此函数中会调用Url黑边名单过滤器、Url回调器、Content回调器
        Args:
            url: 要获取的url
            curr_deep: 当前深度
            extend: 附加数据
        """
        if curr_deep >= self.__max_deep:
            return
        if url in self.__visited_url:
            return
        self.__visited_url.add(url)
        try:
            if not hasattr(self.__local, "http_client"):
                self.__local.http_client = httplib2.Http('.cache')
            response, content = self.__local.http_client.request(url, 'GET', headers=self.__header)
        except Exception as e:
            print("http error", e)
            return
        if response['status'] == '200' or response['status'] == '304':
            content_str, flag = SFPublic.decode_str(content)
            if not flag:
                print("decode error")
                return
            bs = BeautifulSoup(content_str, 'html.parser')
            for k in self.__text_callback:
                k.callback(url, content_str, bs.title.string, extend)
            link_list = bs.select('a')
            for i in link_list:
                if i.has_attr('href'):
                    url = i.attrs['href']
                if i.has_attr('src'):
                    url = i.attrs['src']
                for k in self.__url_callback:
                    k.callback(url, extend)
                tmp_url = self.__url_filter.filter(url)
                if tmp_url is not None:
                    self.__thread_pool.add_task(self.__get_page, tmp_url, curr_deep + 1, extend)
        else:
            print('status error:', response)
            print(url)

    def start(self, begin_page, deep=1, thread_count=4, wait_exit=True, extend=None):
        """
        开始函数，用于驱动各模块的运行
        Args:
            begin_page: 起始页(或者起始页列表)
            deep: 递归深度
            thread_count: 线程数量
            wait_exit: 是否等待所有结果退出
            extend: 附加数据
        """
        self.__max_deep = deep
        self.__thread_pool.set_work_thread_count(thread_count)
        if isinstance(begin_page, list):
            for page in begin_page:
                self.__thread_pool.add_task(self.__get_page, page, 0, extend)
        elif isinstance(begin_page, str):
            self.__thread_pool.add_task(self.__get_page, begin_page, 0, extend)
        self.__thread_pool.start()
        if wait_exit:
            self.__thread_pool.exit_when_no_task()
            self.__thread_pool.wait_exit()

    def add_task(self, page, start_deep=0, extend=None):
        """
        增加新的采集任务
        Args:
            page: 要采集的页面(集合)
            start_deep: 起始深度
            extend: 附加数据
        """
        if isinstance(page, list):
            for url in page:
                self.__thread_pool.add_task(self.__get_page, url, start_deep, extend)
        else:
            self.__thread_pool.add_task(self.__get_page, page, start_deep, extend)

    def set_url_filter(self, url_filter):
        """
        增加Url过滤器
        Args:
            url_filter: Url过滤器对象
        """
        if not isinstance(url_filter, UrlFilter):
            print(url_filter, 'is not a UrlFilter instance')
            return
        self.__url_filter = url_filter

    def add_url_callback(self, callback):
        """
        增加url回调器
        Args:
            callback:Url回调器
        """
        if not isinstance(callback, UrlCallBack):
            print(callback, 'is not a UrlCallBack instance')
            return
        self.__url_callback.add(callback)

    def add_content_callback(self, callback):
        """
        增加content回调器
        Args:
            callback:Content回调器
        """
        if not isinstance(callback, ContentCallback):
            print(callback, 'is not a ContentCallback instance')
            return
        self.__text_callback.add(callback)

    def max_deep(self):
        """
        获取最大采集深度
        Returns:
            返回最大采集深度
        """
        return self.__max_deep

    def clean_history(self):
        """
        清除历史记录
        Returns:
        """
        self.__visited_url.clear()
