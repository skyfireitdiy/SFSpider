from sfdspider.distributedspider import *
from sfspider.collectorfilter import *
from PyQt5 import QtNetwork, QtCore
import sys


class MyUrlFilter(UrlFilter):
    def filter(self, url):
        if url.startswith('/post-develop-'):
            tmp_url = "http://bbs.tianya.cn" + url
            return tmp_url
        return None


class MyContentCallback(ContentCallback):
    def solve_func(self, url, content, title, extend):
        print(threading.current_thread().getName(), "文章标题：", title, extend)


app = QtCore.QCoreApplication(sys.argv)
server = DistributedSpiderServer()
server.set_url_filter(MyUrlFilter())
server.add_content_callback(MyContentCallback())
server.start_server(QtNetwork.QHostAddress("127.0.0.1"), 1234, "http://bbs.tianya.cn/list-develop-1.shtml", 2, 10, False)
app.exec()
