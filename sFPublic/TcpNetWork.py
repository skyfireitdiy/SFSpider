"""
该文件提供一个TCP服务器（基于QTcpServer封装）
"""

from PyQt5 import QtCore, QtNetwork
from sFPublic import SFPublic
import struct


class TcpServer(QtCore.QObject):
    __server = QtNetwork.QTcpServer()
    __clients = dict()

    new_connection_sgn = QtCore.pyqtSignal(QtNetwork.QTcpSocket)
    server_error_sgn = QtCore.pyqtSignal(int)
    client_error_sgn = QtCore.pyqtSignal(QtNetwork.QTcpSocket, int)
    data_coming_sgn = QtCore.pyqtSignal(QtNetwork.QTcpSocket, bytes)

    def __init__(self):
        super().__init__()
        self.__server.newConnection.connect(self.__new_connection_slot)
        self.__server.acceptError.connect(self.__server_error_slot)

    def listen(self, host, port):
        """
        监听端口
        :param host: ip（主机名）
        :param port: 端口
        :return: 监听结果
        """
        return self.__server.listen(host, port)

    def __ready_read_slot(self, sock):
        """
        数据可读处理
        :param sock:socket
        """
        self.__clients[sock] += sock.readAll()
        pos = 0
        while self.__clients[sock].size() - pos > 4:
            data_len = struct.unpack("i", self.__clients[sock].mid(pos, 4))[0]
            if self.__clients[sock].size() - pos - 4 < data_len:
                return
            self.data_coming_callback(sock, bytes(self.__clients[sock].mid(pos + 4, data_len).data()))
            pos += data_len + 4
        self.__clients[sock].remove(0, pos)

    def data_coming_callback(self, sock, data):
        """
        数据包到来回调
        :param sock:socket
        :param data: 数据
        """
        self.data_coming_sgn.emit(sock, data)

    def __new_connection_slot(self):
        """
        新连接到来处理
        """
        while self.__server.hasPendingConnections():
            new_conn = self.__server.nextPendingConnection()
            new_conn.readyRead.connect(SFPublic.sf_bind(self.__ready_read_slot, new_conn))
            new_conn.error.connect(SFPublic.sf_bind(self.__client_error_slot, new_conn))
            self.__clients[new_conn] = QtCore.QByteArray()
            self.new_connection_sgn.emit(new_conn)

    def __server_error_slot(self, err):
        """
        服务器出现异常（默认处理为打印异常信息）
        :param err: 异常类型
        """
        print(self.__server.errorString())
        self.server_error_sgn.emit(err)

    def __client_error_slot(self, sock, err):
        """
        客户端socket异常（默认处理为打印异常信息，从连接列表中删除该socket）
        :param sock:socket
        :param err:异常类型
        """
        print(sock.errorString())
        sock.disconnectFromHost()
        sock.close()
        self.__clients.pop(sock)
        self.client_error_sgn.emit(sock, err)

    @staticmethod
    def send_data(sock, data):
        """
        发送数据
        :param sock: socket
        :param data:数据
        """
        print("Send Data")
        sock.write(SFPublic.sf_make_pack(data))
        sock.waitForBytesWritten()

    def get_server(self):
        """
        获取原始QTcpServer
        :return:服务器
        """
        return self.__server

    def get_client_list(self):
        """
        获取客户端socket列表
        :return: 客户端列表
        """
        return self.__clients.keys()

    def close(self):
        """
        关闭服务器
        """
        for sock in self.__clients.keys():
            sock.disconnectFromHost()
            sock.close()
        self.__server.close()


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
        print("connect to", host.toString(), port)
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
        print(data)
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
