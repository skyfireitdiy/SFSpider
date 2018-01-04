from collectorFilter import ContentCallback
from bs4 import BeautifulSoup
import re


class MainContentAnalyzer(ContentCallback):
    __min_block_line_count = 1

    def set_min_block_line_count(self, count):
        self.__min_block_line_count = count

    def solve_func(self, url, content, title):
        content = self.__del_style_and_script(content)
        content = self.__del_html_mark(content)
        lines = content.splitlines(False)
        block_data = self.__get_block_data(lines)
        self.set_new_content(self.__get_main_content(block_data, lines))

    @staticmethod
    def __replace_str(m):
        gp = m.groupdict()
        line_count = 0
        for k in gp.values():
            if k is not None:
                line_count += len(k.splitlines()) - 1
        return str('\n').center(line_count, '\n')

    @staticmethod
    def __del_html_mark(content):
        bs = BeautifulSoup(content, 'html.parser')
        return bs.text

    def __get_block_data(self, lines):
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
        re_script = re.compile('(?P<script><script.*?</script>)|(?P<style><style.*?</style>)', flags=re.S | re.I)
        return re_script.sub(self.__replace_str, content)
