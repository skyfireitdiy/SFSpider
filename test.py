# coding=utf-8
from collector import Collector
from collectorFilter import *
from MainContentAnalyzer import MainContentAnalyzer
import os
import time
import threading

'定义自己的Content回调器'


class MyContentCallback(ContentCallback):
    """重写solve_func，处理正文，此处将正文保存在以当前日期命名的文件夹下，文件名为网页标题"""

    def solve_func(self, url, content, title):
        print(threading.current_thread().getName(), "文章标题：", title)
        '生成目录名称'
        folder_name = "news_" + time.strftime("%Y-%m-%d", time.localtime())
        '若目录不存在，创建目录'
        if not os.path.exists(folder_name):
            os.mkdir(folder_name)
        '写入正文'
        with open(folder_name + "/" + title + ".txt", 'w') as fp:
            fp.write(content)


'定义自己的Url回调器'


class MyUrlCallback(UrlCallBack):
    """此处只是打印扫描到了哪个url"""

    @staticmethod
    def callback(url):
        print("get:", url)
        return True


'定义自己的url过滤器'


class MyUrlFilter(UrlFilter):
    """过滤掉含有“sohu”的url"""

    def filter(self, url):
        if url.find('sohu') != -1:
            return False
        return True


'定义一个采集器'
s = Collector()
'生成一个正文提取器（content回调器）'
my_content_callback = MainContentAnalyzer()
'将我们的回调器挂在正文提取器后面，此时我们回调器接收到的内容就是经过正文提取器处理过的内容了，如果后面还有处理，还可以再挂回调器'
my_content_callback.set_next_callback(MyContentCallback())
'将Content回调器加入收集器'
s.add_content_callback(my_content_callback)
'添加我们的url回调器'
s.add_url_callback(MyUrlCallback())
'添加我们的url过滤器'
s.set_url_filter(MyUrlFilter())
'开始采集网页，采集深度为2，使用8个线程采集，起始URL为http://news.baidu.com（起始网页不会被黑名单过滤器过滤掉）'
s.start('http://news.baidu.com', 2, 8, True)
