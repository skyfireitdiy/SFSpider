# coding=utf-8

import threading
from bs4 import BeautifulSoup
from sfpublic import toolfunc
from sfpublic.threadpool import ThreadPool
from sfspider.collectorfilter import ContentCallback
from sfspider.collectorfilter import UrlCallBack
from sfspider.collectorfilter import UrlFilter
from sfspider.netgetter import DefaultNetGetter
from sfspider.netgetter import NetGetter

"""
网页收集器（不支持js执行）
"""


class Collector(object):
    def __init__(self):
        print("init")
        self._local = threading.local()
        self._max_deep = 1
        self._page_set = set()
        self._url_callback = set()
        self._text_callback = set()
        self._UrlFilter = UrlFilter
        self._visited_url = set()
        self._thread_pool = ThreadPool()
        self._visited_url_lock = threading.Lock()
        self._GetterType = DefaultNetGetter

    def set_getter(self, getter_type):
        """
        设置getter类型
        :param getter_type: Getter的类型(必须为sfspider.netgetter.NetGetter的子类)
        :return:
        """
        if not issubclass(getter_type, NetGetter):
            print("getter_type must be subclass of sfspider.netgetter.NetGetter")
            return
        self._GetterType = getter_type

    def get_page(self, url, curr_deep, extend=None):
        """
        获取页面，关键函数，使用深度优先搜索
        此函数中会调用Url黑边名单过滤器、Url回调器、Content回调器
        Args:
            url: 要获取的url
            curr_deep: 当前深度
            extend: 附加数据
        """
        if curr_deep >= self._max_deep:
            return
        self._visited_url_lock.acquire()
        if url in self._visited_url:
            self._visited_url_lock.release()
            return
        self._visited_url.add(url)
        self._visited_url_lock.release()
        if not hasattr(self._local, "http_client"):
            self._local.http_client = self._GetterType()
        content = self._local.http_client.get(url, extend)
        if content is None:
            print("get page error", url)
            return
        content_str, flag = toolfunc.sf_decode_str(content)
        if not flag:
            print("decode error, maybe binary")
            # 注意：此处代码在内容无法解析为字符串时调用（比如图片、文件等）
            for k in self._text_callback:
                k.callback(url, content, "", extend)
            return
        bs = BeautifulSoup(content_str, 'html.parser')
        for k in self._text_callback:
            k.callback(url, content_str, bs.title.string, extend)
        link_list = bs.select('a')
        url_list = set()
        for i in link_list:
            tmp_url = None
            if i.has_attr('href'):
                tmp_url = i.attrs['href']
            if i.has_attr('src'):
                tmp_url = i.attrs['src']
            if tmp_url is not None:
                url_list.add(tmp_url)
        for tmp_url in url_list:
            if tmp_url is not None:
                for k in self._url_callback:
                    k.callback(tmp_url, extend)
                tmp_url = self._UrlFilter().filter(tmp_url)
            if tmp_url is not None:
                self._thread_pool.add_task(self.get_page, tmp_url, curr_deep + 1, extend)

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
        self._max_deep = deep
        self._thread_pool.set_work_thread_count(thread_count)
        if isinstance(begin_page, list):
            for page in begin_page:
                self._thread_pool.add_task(self.get_page, page, 0, extend)
        elif isinstance(begin_page, str):
            self._thread_pool.add_task(self.get_page, begin_page, 0, extend)
        self._thread_pool.start()
        if wait_exit:
            self._thread_pool.exit_when_no_task()
            self._thread_pool.wait_exit()

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
                self._thread_pool.add_task(self.get_page, url, start_deep, extend)
        else:
            self._thread_pool.add_task(self.get_page, page, start_deep, extend)

    def set_url_filter(self, url_filter):
        """
        增加Url过滤器
        Args:
            url_filter: Url过滤器类
        """
        if not issubclass(url_filter, UrlFilter):
            print(url_filter, 'is not a subclass of UrlFilter')
            return
        self._UrlFilter = url_filter

    def add_url_callback(self, callback):
        """
        增加url回调器
        Args:
            callback:Url回调器
        """
        if not isinstance(callback, UrlCallBack):
            print(callback, 'is not a UrlCallBack instance')
            return
        self._url_callback.add(callback)

    def add_content_callback(self, callback):
        """
        增加content回调器
        Args:
            callback:Content回调器
        """
        if not isinstance(callback, ContentCallback):
            print(callback, 'is not a ContentCallback instance')
            return
        self._text_callback.add(callback)

    def max_deep(self):
        """
        获取最大采集深度
        Returns:
            返回最大采集深度
        """
        return self._max_deep

    def clean_history(self):
        """
        清除历史记录
        Returns:
        """
        self._visited_url_lock.acquire()
        self._visited_url.clear()
        self._visited_url_lock.release()
