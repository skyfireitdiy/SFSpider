from collector import Collector
from collectorFilter import *
from MainContentAnalyzer import MainContentAnalyzer
import os
import time


class MyContentCallback(ContentCallback):
    def solve_func(self, url, content, title):
        print("文章标题：",title)
        folder_name = "news_" + time.strftime("%Y-%m-%d", time.localtime())
        if not os.path.exists(folder_name):
            os.mkdir(folder_name)
        with open(folder_name+"/"+title+".txt", 'w') as fp:
            fp.write(content)


class MyUrlFilter(PassUrlFilter):
    def filter(self, url):
        print("get:", url)
        return True


s = Collector()
my_callback = MainContentAnalyzer()
my_callback.set_next_call_back(MyContentCallback())
s.add_content_callback(my_callback)
s.add_pass_url_filter(MyUrlFilter())
s.start('http://news.baidu.com', 2)
