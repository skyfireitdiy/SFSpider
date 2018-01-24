# coding=utf-8

import re

from bs4 import BeautifulSoup

from sFSpider.collectorFilter import ContentCallback


class MainContentAnalyzer(ContentCallback):
    """
    正文抽取Content过滤器
    """

    def __init__(self):
        ContentCallback.__init__(self)
        self.__min_block_line_count = 1

    def set_min_block_line_count(self, count):
        """
        设置最小块大小，一般保持不变
        Args:
            count:最小块行数
        """
        self.__min_block_line_count = count

    def solve_func(self, url, content, title):
        """
        处理流程，该流程将正文抽取出来，替换原来的content
        Args:
            url:要处理的url
            content:要处理的内容
            title:标题
        """
        content = self.__del_style_and_script(content)
        content = self.__del_html_mark(content)
        lines = content.splitlines(False)
        block_data = self.__get_block_data(lines)
        self.set_new_content(self.__get_main_content(block_data, lines))

    @staticmethod
    def __replace_callback(m):
        """
        正则表达式匹配回调函数，将匹配到的行替换为换行符
        Args:
            m:匹配到的字符串
        Return:
            替换后的字符串，为换行符的组合
        """
        gp = m.groupdict()
        line_count = 0
        for k in gp.values():
            if k is not None:
                line_count += len(k.splitlines()) - 1
        return str('\n').center(line_count, '\n')

    @staticmethod
    def __del_html_mark(content):
        """
        清除HTML标记
        Args:
            content:要操作的内容
        Returns:
            去掉html标记的内容
        """
        bs = BeautifulSoup(content, 'html.parser')
        return bs.text

    def __get_block_data(self, lines):
        """
        计算block数据，使用类似卷积的方法，数据中每个元素的数值为 (前N行字数)+(当前行字数)+(后N行字数)
        Args:
            lines:内容分割后的每行数据
        Returns:
            计算后的文字密集列表
        """
        blocks_data = list()
        for i in range(len(lines)):
            word_count = 0
            for t in range(i - self.__min_block_line_count, i + self.__min_block_line_count):
                if 0 < t < len(lines):
                    word_count += len(lines[t])
            blocks_data.append(word_count)
        return blocks_data

    @staticmethod
    def __get_main_content(blocks_data, lines):
        """
        抽取正文
        Args:
            blocks_data:文字密集列表
            lines:内容分割后的行数据
        Returns:
            正文
        """
        center = blocks_data.index(max(blocks_data))
        min_line_num = center
        max_line_num = center
        for i in range(center, -1, -1):
            if blocks_data[i] != 0:
                min_line_num = i
            else:
                break
        for i in range(center, len(blocks_data)):
            if blocks_data[i] != 0:
                max_line_num = i
            else:
                break
        return '\n'.join(lines[min_line_num: max_line_num])

    def __del_style_and_script(self, content):
        """
        删除网页script内容和style内容
        Args:
            content:网页内容
        Returns:
            取出script和style后的内容
        """
        re_script = re.compile('(?P<script><script.*?</script>)|(?P<style><style.*?</style>)', flags=re.S | re.I)
        return re_script.sub(self.__replace_callback, content)
