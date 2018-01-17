# coding=utf-8
import threading


class UrlFilter:
    """
    Url过滤器
    """

    def __init__(self):
        pass

    @staticmethod
    def filter(url):
        """
        Url过滤判定
        Args：
            url:要访问的url
        Returns:
            返回要访问的URL，如果拒绝访问则返回None
        """
        return url


class UrlCallBack:
    """
    网页url处理回调器
    """

    __next_callback = None
    __pre_callback = None
    __local = threading.local()
    __local.__url = str()
    __local.__extend = dict()

    def __init__(self):
        pass

    def set_new_url(self, url):
        """
        设置新的url，替换旧的url
        Args:
            url:新的url
        """
        self.__local.__url = url

    def solve_func(self, url, extend):
        """
        处理过程，该方法应该被重写
        Args:
            url:要处理的url
            extend:附加数据
        """
        pass

    def callback(self, url, extend):
        """
        回调接口（不应修改）
        Args:
            url:要处理的url
            extend: 附加数据
        """
        self.__local.__url = url
        self.__local.__extend = extend
        if self.__pre_callback is not None:
            self.__pre_callback.callback(self.__local.__url, self.__local.__extend)
        self.solve_func(self.__local.__url, self.__local.extend)
        if self.__next_callback is not None:
            self.__next_callback.callback(self.__local.__url, self.__local.__extend)

    def set_next_callback(self, next_callback):
        """
        设置下一级回调器，将在本级处理函数处理完毕后调用
        Args:
            next_callback:下级Url回调器
        """
        if not isinstance(next_callback, UrlCallBack):
            print(next_callback, 'is not a UrlCallBack instance')
        self.__next_callback = next_callback

    def set_pre_callback(self, pre_callback):
        """
        设置上一级回调器，将在本级回调过程调用前调用
        Args:
            pre_callback:上级Url回调器
        """
        if not isinstance(pre_callback, UrlCallBack):
            print(pre_callback, 'is not a UrlCallBack instance')
        self.__pre_callback = pre_callback

    @property
    def url(self):
        """
        获取url
        Returns:
            当前url
        """
        return self.__local.__url


class ContentCallback:
    """
    网页内容回调函数
    """

    __next_callback = None
    __pre_callback = None
    __local = threading.local()
    __local.__url = str()
    __local.__content = str()
    __local.__title = str()
    __local.__extend = dict()

    def __init__(self):
        pass

    def set_new_url(self, url):
        """
        设置新的url
        Args:
            url:新的url
        """
        self.__local.__url = url

    def set_new_content(self, content):
        """
        设置新的内容
        Args:
            content:新的内容
        """
        self.__local.__content = content

    def set_new_title(self, title):
        """
        设置新的标题
        Args:
            title:新标题
        """
        self.__local.__title = title

    def solve_func(self, url, content, title, extend):
        """
        处理过程，应该被重写
        Args:
            url:要处理的url
            content:要处理的内容
            title:要处理的标题
            extend:附加数据
        """
        pass

    def set_next_callback(self, next_callback):
        """
        设置下一级回调器，将在本级处理函数处理完毕后调用
        Args:
            next_callback:下级Content回调器
        """
        if not isinstance(next_callback, ContentCallback):
            print(next_callback, 'is not a ContentCallback instance')
        self.__next_callback = next_callback

    def set_pre_callback(self, pre_callback):
        """
        设置上一级回调器，将在本级回调过程调用前调用
        Args:
            pre_callback:上级Content回调器
        """
        if not isinstance(pre_callback, ContentCallback):
            print(pre_callback, 'is not a ContentCallback instance')
        self.__pre_callback = pre_callback

    def callback(self, url, content, title, extend):
        """
        回调接口（不应修改）
        Args:
            url:要处理的url
            content:要处理的内容
            title:要处理的标题
            extend: 附加数据
        """
        self.__local.__url = url
        self.__local.__content = content
        self.__local.__title = title
        self.__local.__extend = extend
        if self.__pre_callback is not None:
            self.__pre_callback.callback(self.__local.__url, self.__local.__content, self.__local.__title, self.__local.__extend)
        self.solve_func(self.__local.__url, self.__local.__content, self.__local.__title, self.__local.__extend)
        if self.__next_callback is not None:
            self.__next_callback.callback(self.__local.__url, self.__local.__content, self.__local.__title, self.__local.__extend)

    @property
    def url(self):
        """
        获取url
        Returns:
            当前Url
        """
        return self.__local.__url

    @property
    def content(self):
        """
        获取内容
        Returns:
            当前内容
        """
        return self.__local.__content

    @property
    def title(self):
        """
        获取标题
        Returns:
            当前标题
        """
        return self.__local.__title
