

class UrlSet(object):
    """
    Url集合类型
    """
    def contains(self, url):
        """
        是否包含url
        :param url:指定的url
        :return: true表示包含
        """
        return True

    def add(self, url):
        """
        增加一个url
        :param url: 指定的url
        """
        pass

    def remove(self, url):
        """
        删除一个url
        :param url: 指定的url
        """
        pass

    def clear(self):
        """
        清空
        """
        pass

    def get_list(self):
        """
        获取url列表
        :return:
        """
        return list()



class DefaultUrlSet(UrlSet):
    """
    默认的urlset，使用set管理
    """
    def __init__(self):
        super().__init__()
        self._visited_set = set()

    def contains(self, url):
        return url in self._visited_set

    def add(self, url):
        self._visited_set.add(url)

    def remove(self, url):
        self._visited_set.remove(url)

    def clear(self):
        self._visited_set.clear()

    def get_list(self):
        return list(self._visited_set)

