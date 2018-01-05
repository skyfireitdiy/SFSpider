
class PassUrlFilter:

    def filter(self, url):
        return True


class RefuseUrlFilter:

    def filter(self, url):
        return False


class UrlCallBack:
    __next_callback = None
    __pre_callback = None
    __url = str()

    def set_new_url(self, url):
        self.__url = url

    def solve_func(self, url):
        pass

    def callback(self, url):
        self.__url = url
        if self.__pre_callback is not None:
            self.__pre_callback.callback(self.__url)
        self.solve_func(self.__url)
        if self.__next_callback is not None:
            self.__next_callback.callback(self.__url)

    def set_next_callback(self, next_callback):
        if not isinstance(next_callback, UrlCallBack):
            print(next_callback, 'is not a UrlCallBack instance')
        self.__next_callback = next_callback

    def set_pre_callback(self, pre_callback):
        if not isinstance(pre_callback, UrlCallBack):
            print(pre_callback, 'is not a UrlCallBack instance')
        self.__pre_callback = pre_callback

    @property
    def url(self):
        return self.__url


class ContentCallback:
    
    __next_callback = None
    __pre_callback = None
    __url = str()
    __content = str()
    __title = str()

    def set_new_url(self, url):
        self.__url = url

    def set_new_content(self, content):
        self.__content = content

    def set_new_title(self, title):
        self.__title = title

    def solve_func(self, url, content, title):
        pass

    def set_next_callback(self, next_callback):
        if not isinstance(next_callback, ContentCallback):
            print(next_callback, 'is not a ContentCallback instance')
        self.__next_callback = next_callback

    def set_pre_callback(self, pre_callback):
        if not isinstance(pre_callback, ContentCallback):
            print(pre_callback, 'is not a ContentCallback instance')
        self.__pre_callback = pre_callback

    def callback(self, url, content, title):
        self.__url = url
        self.__content = content
        self.__title = title
        if self.__pre_callback is not None:
            self.__pre_callback.callback(self.__url, self.__content, self.__title)
        self.solve_func(self.__url, self.__content, self.__title)
        if self.__next_callback is not None:
            self.__next_callback.callback(self.__url, self.__content, self.__title)

    @property
    def url(self):
        return self.__url

    @property
    def content(self):
        return self.__content

    @property
    def title(self):
        return self.__title
