# coding:utf-8

import httplib2
from collectorFilter import PassUrlFilter
from collectorFilter import RefuseUrlFilter
from collectorFilter import UrlCallBack
from collectorFilter import ContentCallback
from bs4 import BeautifulSoup


class Collector:
    __page_set = set()
    __http_client = httplib2.Http('.cache')
    __max_deep = 1
    __url_callback = set()
    __text_callback = set()
    __pass_url = set()
    __refuse_url = set()
    __visited_url = set()
    __codec_set = ["utf_8", "gb18030", "utf_8_sig", "gbk", "gb2312", "ascii", "big5", "cp424", "cp437", "cp500",
                   "cp850", "cp852", "cp855", "cp856", "cp857", "cp858", "cp860", "cp861", "cp862", "cp863", "cp864",
                   "cp865", "cp866", "cp869", "cp874", "cp875", "cp932", "cp949", "cp950", "cp1006", "cp1026", "cp1125",
                   "cp1140", "cp1250", "cp1251", "cp1252", "cp1253", "cp1254", "cp1255", "cp1256", "cp1257", "cp1258",
                   "cp65001", "euc_jp", "euc_jis_2004", "euc_jisx0213", "euc_kr", "hz", "cp720", "cp737", "cp775",
                   "iso2022_jp", "iso2022_jp_1", "iso2022_jp_2", "iso2022_jp_2004", "iso2022_jp_3", "iso2022_jp_ext",
                   "iso2022_kr", "latin_1", "iso8859_2", "iso8859_3", "iso8859_4", "iso8859_5", "iso8859_6",
                   "iso8859_7", "iso8859_8", "iso8859_9", "iso8859_10", "iso8859_11", "iso8859_13", "iso8859_14",
                   "iso8859_15", "iso8859_16", "johab", "koi8_r", "koi8_t", "koi8_u", "kz1048", "mac_cyrillic",
                   "mac_greek", "mac_iceland", "mac_latin2", "mac_roman", "mac_turkish", "ptcp154", "shift_jis",
                   "shift_jis_2004", "shift_jisx0213", "utf_32", "utf_32_be", "utf_32_le", "utf_16", "utf_16_be",
                   "utf_16_le", "utf_7", "idna", "mbcs", "palmos", "punycode", "big5hkscs", "cp037", "cp273",
                   "raw_unicode_escape", "undefined", "unicode_escape", "unicode_internal", "base64_codec [1]",
                   "bz2_codec", "hex_codec", "quopri_codec", "uu_codec", "zlib_codec", "rot_13"]

    def __init__(self):
        self.__header = dict()
        self.__header['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) ' \
                                      'Chrome/63.0.3239.84 Safari/537.36'

    def __decode_str(self, content):
        flag = False
        content_str = ""
        for code_name in self.__codec_set:
            try:
                content_str = content.decode(code_name)
                flag = True
                break
            except Exception as e:
                print(e)
                continue
        return content_str, flag

    def __get_page(self, url, curr_deep):
        if curr_deep == self.__max_deep:
            return
        if url in self.__visited_url:
            return
        self.__visited_url.add(url)
        try:
            response, content = self.__http_client.request(url, 'GET', headers=self.__header)
        except Exception as e:
            print("http error", e)
            return
        if response['status'] == '200' or response['status'] == '304':
            content_str, flag = self.__decode_str(content)
            if not flag:
                print("decode error")
                return
            bs = BeautifulSoup(content_str, 'html.parser')
            for k in self.__text_callback:
                k.callback(url, content_str, bs.title.string)
            link_list = bs.select('a')
            for i in link_list:
                if i.has_attr('href'):
                    url = i.attrs['href']
                if i.has_attr('src'):
                    url = i.attrs['src']
                for k in self.__url_callback:
                    k.callback(url)
                flag = False
                for k in self.__refuse_url:
                    if k.filter(url):
                        flag = True
                        break
                if flag:
                    continue

                flag = False
                for k in self.__pass_url:
                    if k.filter(url):
                        flag = True
                        break
                if flag:
                    self.__get_page(url, curr_deep + 1)
        else:
            print('status error:', response)
            print(content)

    def start(self, begin_page, deep=1):
        self.__max_deep = deep
        self.__get_page(begin_page, 0)

    def add_pass_url_filter(self, pass_url):
        if not isinstance(pass_url, PassUrlFilter):
            print(pass_url, 'is not a PassUrlFilter instance')
            return
        self.__pass_url.add(pass_url)

    def add_refuse_url_filter(self, refuse_url):
        if not isinstance(refuse_url, RefuseUrlFilter):
            print(refuse_url,'is not a RefuseUrlFilter instance')
        self.__refuse_url.add(refuse_url)

    def add_url_callback(self, callback):
        if not isinstance(callback, UrlCallBack):
            print(callback, 'is not a UrlCallBack instance')
            return
        self.__url_callback.add(callback)

    def add_content_callback(self, callback):
        if not isinstance(callback, ContentCallback):
            print(callback, 'is not a ContentCallback instance')
            return
        self.__text_callback.add(callback)

