# SFSpider

**SkyFire**

**E-mail:skyfireitdiy@hotmail.com**

**QQ:1513008876**



`SFSpider`是一个通用的网络爬虫框架，目前包括线程池（`ThreadPool`）、收集器（`Collector`）、Url过滤器（`UrlFilter`）、url回调器（`UrlCallBack`）、content回调器（`ContentCallback`），以及一个用于抽取网页正文的正文抽取器（`MainContentAnalyzer`）

* 模块介绍

    * `ThreadPool`：供采集器使用（也可以单独抽取出来使用），实现多线程采集，提高采集效率。
    * `Collector`：采集器。该模块主要负责url的访问，采用深度优先遍历采集网页。在采集过程中调用`UrlFilter`来确定是否需要访问，页面采集完成后，会调用`UrlCallBack`和`ContentCallback`分别对网页中的Url和网页内容处理。
    * `UrlFilter`：url过滤器，url传到此模块，如果模块函数返回`True`，表示允许下一步访问，采集器会对该url进行采集，返回`False`则不会对该Url进行下一步采集。
    * `UrlCallBack`：url回调器。网页采集完毕后，采集器会扫描网页上的`<a>`标签链接，对于每个链接，都会调用此模块处理。
    * `ContentCallback`：content回调器。网页采集完毕后，采集器会将网页url、网页标题、网页html正文传递到此模块处理。
    * `MainContentAnalyzer`：网页正文抽取器。为`ContentCallback`的一个实现，用于抽取出html网页的正文。

* 模块结构

    `Collector`运行过程中，与`UrlFilter`、`UrlCallBack`、`ContentCallback`工作的流程如下图所示（`ThreadPool`为`Collector`内部使用的一个模块，用户不比直接对其操作，所以在此处没有画出）：

    ```flow
    start=>start: 开始
    end=>end: 结束
    collector=>operation: 采集网页
    scan_url=>operation: 扫描网页中的URL
    url_callback=>operation: url回调
    content_calback=>operation: content回调
    pass_url=>condition: 是否通行？
    next=>operation: 下一轮采集
    start->collector->scan_url->url_callback->content_calback->pass_url
    pass_url(no)->end
    pass_url(yes,right)->next->end
    ```

    ​在采集器中，可以有多个url白名单过滤器、url黑名单过滤器、url回调器、content回调器，而回调器可以挂接上下级回调器，结构如下：

    ```mermaid
    graph TD;
    采集器-->Url过滤器
    采集器-->Url回调器1
    Url回调器1-->Url回调器2
    Url回调器2-->Url回调器3
    Url回调器3-->Url回调器.
    采集器-->Url回调器4
    Url回调器4-->Url回调器5
    Url回调器5-->Url回调器6
    Url回调器6-->Url回调器..
    采集器-->Url回调器7
    Url回调器7-->Url回调器8
    Url回调器8-->Url回调器9
    Url回调器9-->Url回调器...
    采集器-->Content回调器1
    Content回调器1-->Content回调器2
    Content回调器2-->Content回调器3
    Content回调器3-->Content回调器.
    采集器-->Content回调器4
    Content回调器4-->Content回调器5
    Content回调器5-->Content回调器6
    Content回调器6-->Content回调器..
    采集器-->Content回调器7
    Content回调器7-->Content回调器8
    Content回调器8-->Content回调器9
    Content回调器9-->Content回调器...
    ```



* 示例程序

    * 代码中含有`test.py`程序，演示了对框架的使用：

        代码如下:

        ```python
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

        '定义自己的url过滤器'

        class MyUrlFilter(UrlFilter):
            """过滤含有“/post-develop-”的url，追加前缀"""

            def filter(self, url):
                if url.startswith('/post-develop-'):
                    tmp_url = "http://bbs.tianya.cn" + url
                    return tmp_url
                return None

        '定义一个采集器'
        s = Collector()
        '生成一个正文提取器（content回调器）'
        my_content_callback = MainContentAnalyzer()
        '将我们的回调器挂在正文提取器后面，此时我们回调器接收到的内容就是经过正文提取器处理过的内容了，如果后面还有处理，还可以再挂回调器'
        my_content_callback.set_next_callback(MyContentCallback())
        '将Content回调器加入收集器'
        s.add_content_callback(my_content_callback)
        '添加我们的url过滤器'
        s.set_url_filter(MyUrlFilter())
        '开始采集网页，采集深度为2，使用8个线程采集'
        s.start('http://bbs.tianya.cn/list-develop-1.shtml', 2, 8, True)
        ```

* 注意

    * 在继承URL回调器和Content回调器时，如果对象中添加了成员变量，必须放到TLS（线程局部存储）中，防止线程间对成员变量的访问互相影响，如下：

        ```cpp
        class MyContentCallback(ContentCallback):
        	__local = threading.local()
            # ...
            def solve_func(self, url, content, title):
        		__local.x = 10
                # ...
                # use __local.x
        ```


* 依赖的python包（不包括内置）

    * ​httplib2
    * BeautifulSoup
    * snownlp
    * textblob

    可使用以下命令安装：

    ```shell
    pip3 install httplib2
    pip3 install beautifulsoup4
    pip3 install snownlp
    pip3 install -U textblob
    python3 -m textblob.download_corpora
    ```

    ​

