from sfpublic.tcpnetwork import *
from sfpublic import toolfunc
from sfspider import collector
from PyQt5 import QtNetwork
import httplib2
from bs4 import BeautifulSoup
import sys
from PyQt5 import QtCore


class MsgSender(QtCore.QObject):
    """
    发送信息辅助类，主要为了在线程池以及tcp socket间传递消息
    """
    client_send_sgn = QtCore.pyqtSignal(bytes)
    server_send_sgn = QtCore.pyqtSignal(QtNetwork.QTcpSocket, bytes)

    def __init__(self):
        super().__init__()


class DistributedSpiderServer(collector.Collector):
    """
    分布式爬虫主节点
    """
    _server = TcpServer()
    _clients = dict()
    _server_task_count = 0

    def __init__(self):
        super().__init__()
        self._server.data_coming_sgn.connect(self._server_msg_coming_slot)
        self._server.new_connection_sgn.connect(self._new_connection_slot)
        self._server.client_error_sgn.connect(self._sock_error_slot)

    def _server_msg_coming_slot(self, sock, data):
        """
        服务器消息到来处理函数
        :param sock: 来源Socket
        :param data: 数据
        """
        obj = toolfunc.sf_unpack_data(data)
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
            for i in range(len(self._clients[sock]["task"])):
                if self._clients[sock]["task"][i]["page"] == data_["url"]:
                    del self._clients[sock]["task"][i]
                    break
            for con_cb in self._text_callback:
                con_cb.callback(data_["url"], data_["content"], data_["title"], data_["extend"])

    def _new_connection_slot(self, sock):
        """
        新连接到来处理（创建数据结构）
        :param sock: 新连接Socket
        """
        print("new connection")
        self._clients[sock] = dict()
        self._clients[sock]["task"] = list()

    def _sock_error_slot(self, sock, err):
        """
        Socket异常处理
        :param sock: 出现异常的Socket
        :param err: 错误码
        """
        task_list = self._clients[sock]["task"]
        self._clients.pop(sock)
        print(sock.errorString(), err)
        self._visited_url_lock.acquire()
        for task in task_list:
            self._visited_url.remove(task["page"])
        self._visited_url_lock.release()
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
        if not self._server.listen(local_host, local_port):
            print("Listen on", local_host, ":", local_port, " error")
        self.start(begin_page, deep, thread_count, wait_exit, extend)

    def get_min_task_client(self):
        """
        获取所有客户端任务量最小的机器
        :return:最小任务量sock，最小值
        """
        ret_sock = None
        task_num = sys.maxsize
        for sock, task in self._clients.items():
            if task_num > len(task["task"]):
                ret_sock = sock
                task_num = len(task["task"])
        return ret_sock, task_num

    def distribute_task(self, sock, url, curr_deep, extend):
        """
        分发任务
        :param sock: 目标Socket
        :param url: 任务url
        :param curr_deep: 当前深度
        :param extend: 附加数据
        """
        task = dict()
        task["page"] = url
        task["start_deep"] = curr_deep
        task["extend"] = extend
        self._clients[sock]["task"].append(task)
        self._local.msg_sender.server_send_sgn.emit(sock, toolfunc.sf_pack_data("task", task))

    def get_page(self, url, curr_deep, extend=None):
        """
        获取页面，关键函数，使用深度优先搜索
        此函数中会调用Url黑边名单过滤器、Url回调器、Content回调器
        Args:
            url: 要获取的url
            curr_deep: 当前深度
            extend: 附加数据
        """
        if not hasattr(self._local, "msg_sender"):
            self._local.msg_sender = MsgSender()
            self._local.msg_sender.server_send_sgn.connect(self._server.send_data)
        if curr_deep >= self._max_deep:
            return
        self._visited_url_lock.acquire()
        if url in self._visited_url:
            self._visited_url_lock.release()
            return
        self._visited_url_lock.release()
        sock, task_count = self.get_min_task_client()
        if sock is None or task_count > self._server_task_count:
            self._server_task_count += 1
            super().get_page(url, curr_deep, extend)
            self._server_task_count -= 1
        else:
            self._visited_url_lock.acquire()
            self._visited_url.add(url)
            self._visited_url_lock.release()
            self.distribute_task(sock, url, curr_deep, extend)

    def clean_history(self):
        super().clean_history()
        data = dict()
        pkg = toolfunc.sf_pack_data("clear_history", data)
        if not hasattr(self._local, "msg_sender"):
            self._local.msg_sender = MsgSender()
            self._local.msg_sender.server_send_sgn.connect(self._server.send_data)
        for sock in self._clients.keys():
            self._local.msg_sender.server_send_sgn.emit(sock, pkg)


class DistributedSpiderClient(DistributedSpiderServer):
    """
    分布式爬虫从节点
    """
    __client = TcpClient()

    def __init__(self):
        super().__init__()
        self.__client.data_coming_sgn.connect(self._client_msg_coming_slot)

    def _client_msg_coming_slot(self, data):
        """
        客服端消息到来响应
        :param data: 数据
        """
        obj = toolfunc.sf_unpack_data(data)
        if obj is None:
            return
        type_ = obj["type"]
        data_ = obj["data"]
        if type_ == "task":
            self.add_task(data_["page"], data_["start_deep"], data_["extend"])
            return
        if type_ == "clear_history":
            self.clean_history()

    def _server_msg_coming_slot(self, sock, data):
        """
        客户端服务器消息到来响应
        :param sock: Socket
        :param data: 数据
        """
        obj = toolfunc.sf_unpack_data(data)
        if obj is None:
            return
        type_ = obj["type"]
        data_ = obj["data"]
        if type_ == "url_list":
            self.__client.send_data(toolfunc.sf_pack_data("url_list", data_))
            return
        if type_ == "content":
            for i in range(len(self._clients[sock]["task"])):
                if self._clients[sock]["task"][i]["page"] == data_["url"]:
                    del self._clients[sock]["task"][i]
                    break
            self.__client.send_data(toolfunc.sf_pack_data("content", data_))
            return

    def start_client(self, local_host, local_port, server_host, server_port, deep=1, thread_count=4):
        """
        开始函数，用于驱动各模块的运行
        Args:
            local_host: 本地监听IP
            local_port: 本地监听端口
            server_host: 服务器ip
            server_port: 服务器端口
            deep: 递归深度
            thread_count: 线程数量
        """
        if local_host is None:
            local_host = QtNetwork.QHostAddress.Any
        if not self._server.listen(local_host, local_port):
            print("Listen on", local_host, ":", local_port, " error")
        self.start(None, deep, thread_count, False, None)
        self.__client.connect_to_host(server_host, server_port)

    def _report_urls(self, url_list, curr_deep, extend):
        """
        向上级节点汇报url列表
        :param url_list: url列表
        :param curr_deep: 深度
        :param extend: 附加数据
        """
        data = dict()
        data["url_list"] = url_list
        data["curr_deep"] = curr_deep
        data["extend"] = extend
        self._local.msg_sender.client_send_sgn.emit(toolfunc.sf_pack_data("url_list", data))

    def _report_content(self, url, content, title, extend):
        """
        向上级节点汇报内容
        :param url: url日志
        :param content: 内容
        :param title: 标题
        :param extend: 附加数据
        """
        data = dict()
        data["url"] = url
        data["content"] = content
        data["title"] = title
        data["extend"] = extend
        self._local.msg_sender.client_send_sgn.emit(toolfunc.sf_pack_data("content", data))

    def get_page(self, url, curr_deep, extend=None):
        """
        获取页面，关键函数，使用深度优先搜索
        此函数中会调用Url黑边名单过滤器、Url回调器、Content回调器
        Args:
            url: 要获取的url
            curr_deep: 当前深度
            extend: 附加数据
        """
        if not hasattr(self._local, "msg_sender"):
            self._local.msg_sender = MsgSender()
            self._local.msg_sender.server_send_sgn.connect(self._server.send_data)
            self._local.msg_sender.client_send_sgn.connect(self.__client.send_data)
        if curr_deep >= self._max_deep:
            self._report_content(url, "", "", extend)
            return
        self._visited_url_lock.acquire()
        if url in self._visited_url:
            self._visited_url_lock.release()
            self._report_content(url, "", "", extend)
            return
        self._visited_url.add(url)
        self._visited_url_lock.release()
        sock, task_count = self.get_min_task_client()
        if sock is None or task_count > self._server_task_count:
            try:
                self._server_task_count += 1
                if not hasattr(self._local, "http_client"):
                    self._local.http_client = httplib2.Http('.cache')
                response, content = self._local.http_client.request(url, 'GET', headers=self._header)
            except Exception as e:
                print("http error", e)
                self._report_content(url, "", "", extend)
                return
            if response['status'] == '200' or response['status'] == '304':
                content_str, flag = toolfunc.sf_decode_str(content)
                if not flag:
                    print("decode error")
                    self._report_content(url, "", "", extend)
                    return
                bs = BeautifulSoup(content_str, 'html.parser')
                self._report_content(url, content_str, bs.title.string, extend)
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
                self._report_urls(list(url_list), curr_deep + 1, extend)
            else:
                print('status error:', response)
                self._report_content(url, "", "", extend)
                print(url)
            self._server_task_count -= 1
        else:
            self.distribute_task(sock, url, curr_deep, extend)
