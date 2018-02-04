import httplib2


class NetGetter(object):
    def get(self, url, extend):
        """
        get(self, url, extend) -> bytes
        获取网页内容
        :param url: 要获取的url
        :param extend: 附加信息
        :return: 状态信息，网页内容
        """
        pass


class DefaultNetGetter(NetGetter):
    """
    默认网页获取类
    """
    def __init__(self):
        self._http_client = httplib2.Http(".cache")
        self._header = dict()
        self._header['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) ' \
                                     'Chrome/63.0.3239.84 Safari/537.36'

    def get(self, url, extend):
        """
        get(self, url, extend)  -> bytes
        使用 httplib2 库获取网页内容
        :param url: 网址
        :param extend: 附加信息（此处未使用）
        :return: 网页内容
        """
        try:
            response, content = self._http_client.request(url, 'GET', headers=self._header)
            if response["status"] == "200" or response["status"] == "304":
                return content
            else:
                print('status error:', response, url)
                return None
        except Exception as e:
            print("http exception", e, url)
            return None
