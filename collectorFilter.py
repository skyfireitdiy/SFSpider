
class PassUrlFilter:

    def filter(self, url):
        return True


class RefuseUrlFilter:

    def filter(self, url):
        return False


class UrlCallBack:
    __next_callback = None
    __url = str()

    def set_new_url(self, url):
        self.__url = url

    def solve_func(self, url):
        pass

    def callback(self, url):
        self.__url = url
        self.solve_func(url)
        if self.__next_callback is not None:
            self.__next_callback.callback(url)

    def set_next_call_back(self, next_call_back):
        if not isinstance(next_call_back, UrlCallBack):
            print(next_call_back, 'is not a UrlCallBack instance')
        self.__next_callback = next_call_back

    @property
    def url(self):
        return self.__url


class ContentCallback:

    __next_callback = None
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

    def set_next_call_back(self, next_call_back):
        if not isinstance(next_call_back, ContentCallback):
            print(next_call_back, 'is not a ContentCallback instance')
        self.__next_callback = next_call_back

    def callback(self, url, content, title):
        self.__url = url
        self.__content = content
        self.__title = title
        self.solve_func(url, content, title)
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
