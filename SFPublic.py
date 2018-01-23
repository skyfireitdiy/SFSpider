import struct


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
