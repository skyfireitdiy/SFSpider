from DistributedSpider.TcpServer import TcpServer
from DistributedSpider.TcpClient import TcpClient
from SFSpider import collector
from SFSpider.collectorFilter import *
from PyQt5 import QtNetwork
import httplib2
from bs4 import BeautifulSoup
from SFPublic import SFPublic
import sys


class DistributedSpiderServer(collector.Collector):
    __server = TcpServer()
    __clients = dict()
    __server_task_count = 0

    def __init__(self):
        super().__init__()
        self.__server.data_coming_sgn.connect(self._server_msg_coming_slot)
        self.__server.new_connection_sgn.connect(self.__new_connection_slot)
        self.__server.client_error_sgn.connect(self.__sock_error_slot)

    def _server_msg_coming_slot(self, sock, data):
        obj = SFPublic.sf_unpack_data(data)
        if obj is None:
            return
        type_ = obj["type"]
        data_ = obj["data"]
        if type_ == "url_list":
            for url in data_["url_list"]:
                for k in self._url_callback:
                    k.callback(url, data_["extend"])
                tmp_url = self._url_filter.filter(url)
                if tmp_url is not None:
                    self.add_task(tmp_url, data_["curr_deep"], data_["extend"])
            return
        if type_ == "content":
            for i in range(len(self.__clients[sock]["task"])):
                if self.__clients[sock]["task"][i]["page"] == data_["url"]:
                    del self.__clients[sock]["task"][i]
                    break
            for con_cb in self._text_callback:
                con_cb.callback(data_["url"], data_["content"], data_["title"], data_["extend"])

    def __new_connection_slot(self, sock):
        self.__clients[sock] = dict()
        self.__clients[sock]["task"] = list()

    def __sock_error_slot(self, sock, err):
        task_list = self.__clients[sock]["task"]
        self.__clients.pop(sock)
        print(sock.errorString(), err)
        for task in task_list:
            self.add_task(task["page"], task["start_deep"], task["extend"])

    def start_server(self, local_host, local_port, begin_page, deep=1, thread_count=4, wait_exit=True, extend=None):
        """
        开始函数，用于驱动各模块的运行
        Args:
            local_host: 本地监听IP（传递None为任意IP）
            local_port: 本地监听端口
            begin_page: 起始页(或者起始页列表)
            deep: 递归深度
            thread_count: 线程数量
            wait_exit: 是否等待所有结果退出
            extend: 附加数据
        """
        if local_host is None:
            local_host = QtNetwork.QHostAddress.Any
        if not TcpServer.listen(local_host, local_port):
            print("Listen on", local_host, ":", local_port, " error")
        super().start(begin_page, deep, thread_count, wait_exit, extend)

    def get_min_task_client(self):
        """
        获取所有客户端任务量最小的机器
        :return:最小任务量sock，最小值
        """
        ret_sock = None
        task_num = sys.maxsize()
        for sock, task in self.__clients.items():
            if task_num > len(task):
                ret_sock = sock
                task_num = len(task)
        return ret_sock, task_num

    def distribute_task(self, sock, url, curr_deep, extend):
        task = dict()
        task["page"] = url
        task["start_deep"] = curr_deep
        task["extend"] = extend
        self.__clients[sock]["task"].append(task)
        self.__server.send_data(sock, SFPublic.sf_pack_data("task", task))

    def get_page(self, url, curr_deep, extend=None):
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
        if url in self._visited_url:
            return
        sock, task_count = self.get_min_task_client()
        if sock is None or task_count > self.__server_task_count:
            super().get_page(url, curr_deep, extend)
        else:
            self.distribute_task(sock, url, curr_deep, extend)


class DistributedSpiderClient(DistributedSpiderServer):
    __client = TcpClient

    def __init__(self):
        super().__init__()
        self.__client.data_coming_sgn.connect(self.__client_msg_coming_slot)

    def __client_msg_coming_slot(self, data):
        obj = SFPublic.sf_unpack_data(data)
        if obj is None:
            return
        type_ = obj["type"]
        data_ = obj["data"]
        if type_ == "task":
            self.add_task(data_["page"], data_["start_deep"], data_["extend"])
            return

    def _server_msg_coming_slot(self, sock, data):
        obj = SFPublic.sf_unpack_data(data)
        if obj is None:
            return
        type_ = obj["type"]
        data_ = obj["data"]
        if type_ == "url_list":
            self.__client.send_data(SFPublic.sf_pack_data("url_list", data_))
            return
        if type_ == "content":
            self.__client.send_data(SFPublic.sf_pack_data("content", data_))
            return

    def start_client(self, local_host, local_port, server_host, server_port, begin_page, deep=1, thread_count=4,
                     wait_exit=True, extend=None):
        """
        开始函数，用于驱动各模块的运行
        Args:
            local_host: 本地监听IP
            local_port: 本地监听端口
            server_host: 服务器ip
            server_port: 服务器端口
            begin_page: 起始页(或者起始页列表)
            deep: 递归深度
            thread_count: 线程数量
            wait_exit: 是否等待所有结果退出
            extend: 附加数据
        """
        pass

    def report_urls(self, url_list, curr_deep, extend):
        data = dict()
        data["url_list"] = url_list
        data["curr_deep"] = curr_deep
        data["extend"] = extend
        self.__client.send_data(SFPublic.sf_pack_data("url_list", data))

    def report_content(self, url, content, title, extend):
        data = dict()
        data["url"] = url
        data["content"] = content
        data["title"] = title
        data["extend"] = extend
        self.__client.send_data(SFPublic.sf_pack_data("content", data))

    def get_page(self, url, curr_deep, extend=None):
        if curr_deep >= self.__max_deep:
            return
        if url in self._visited_url:
            return
        sock, task_count = self.get_min_task_client()
        if sock is None or task_count > self.__server_task_count:
            try:
                if not hasattr(self.__local, "http_client"):
                    self.__local.http_client = httplib2.Http('.cache')
                response, content = self.__local.http_client.request(url, 'GET', headers=self.__header)
            except Exception as e:
                print("http error", e)
                return
            self._visited_url.add(url)
            if response['status'] == '200' or response['status'] == '304':
                content_str, flag = SFPublic.sf_decode_str(content)
                if not flag:
                    print("decode error")
                    return
                bs = BeautifulSoup(content_str, 'html.parser')
                self.report_content(url, content_str, bs.title.string, extend)
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
                self.report_urls(url_list, curr_deep + 1, extend)
            else:
                print('status error:', response)
                print(url)
        else:
            self.distribute_task(sock, url, curr_deep, extend)
