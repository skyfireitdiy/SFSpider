import struct
import chardet
import json


def sf_pack_data(type_, data):
    """
    封装数据包
    :param type_: 数据包类型
    :param data: 数据报数据
    :return: json字节数组（utf-8编码）
    """
    if not isinstance(type_, str):
        print("type_ must be an instance of str")
    if not isinstance(data, dict):
        print("data must be an instance of dict")
    ret_data = dict()
    ret_data["type"] = type_
    ret_data["data"] = data
    return json.dumps(ret_data).encode("utf-8")


def sf_unpack_data(data):
    """
    解压数据包
    :param data:字节数组（utf-8编码）
    :return: dict对象
    """
    try:
        obj = json.loads(data.decode("utf-8"))
        return obj
    except Exception as e:
        print(e)
        return None


def sf_bind(func, *args):
    """
    bind，将参数绑定至函数，生成新的函数
    :param func: 要绑定的函数
    :param args: 参数
    :return: 新函数
    """

    def _func(*_args):
        return func(*args, *_args)

    return _func


def sf_make_pack(data):
    """
    打包数据
    :param data: 数据
    :return: 增加了数据长度包头的数据
    """
    return struct.pack("i", len(data)) + data


def sf_decode_str(content):
    """
    网页内容解码器，包含python支持的所有编码，解码成功为止，不保证一定正确
    Args:
        content:网页内容，bytes
    """
    flag = False
    content_str = ""
    codec = chardet.detect(content)["encoding"]
    try:
        content_str = content.decode(codec)
        flag = True
    except Exception as e:
        print(e)
    return content_str, flag
