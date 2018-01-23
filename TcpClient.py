from PyQt5 import QtCore, QtNetwork
import struct
import SFPublic


class TcpClient(QtCore.QObject):
    __client = QtNetwork.QTcpSocket()
    __buffer = QtCore.QByteArray()

    connect_succeed_sgn = QtCore.pyqtSignal()
    socket_error_sgn = QtCore.pyqtSignal(int)
    data_coming_sgn = QtCore.pyqtSignal(bytes)

    def __init__(self):
        super().__init__()
        self.__client.connected.connect(self.__connect_succeed)
        self.__client.error.connect(self.__socket_error_slots)
        self.__client.readyRead.connect(self.__ready_read_slots)

    def connect_to_host(self, host, port):
        """
        连接服务器
        :param host:server IP
        :param port:server 端口
        """
        self.__client.connectToHost(QtNetwork.QHostAddress(host), port)

    def __connect_succeed(self):
        """
        连接成功处理
        """
        print("Connected")
        self.connect_succeed_sgn.emit()

    def __socket_error_slots(self, err):
        """
        socket异常处理
        :param err: 错误码
        """
        print(self.__client.errorString())
        self.socket_error_sgn.emit(err)

    def __ready_read_slots(self):
        """
        有数据可读取响应
        :return:
        """
        self.__buffer += self.__client.readAll()
        pos = 0
        while self.__buffer.size() - pos > 4:
            data_len = struct.unpack("i", self.__buffer.mid(pos, 4))[0]
            if self.__buffer.size() - pos - 4 < data_len:
                return
            self.data_coming_callback(bytes(self.__buffer.mid(pos + 4, data_len).data()))
            pos += data_len + 4

    def data_coming_callback(self, data):
        """
        数据包到来回调函数
        :param data: 数据
        """
        self.data_coming_sgn.emit(data)

    def send_data(self, data):
        """
        发送数据
        :param data:数据
        """
        self.__client.write(SFPublic.sf_make_pack(data))
        self.__client.waitForBytesWritten()

    def close(self):
        """
        关闭socket
        """
        self.__buffer.clear()
        self.__client.disconnectFromHost()
        self.__client.close()

    def get_socket(self):
        """
        获取原生socket
        :return: socket
        """
        return self.__client

