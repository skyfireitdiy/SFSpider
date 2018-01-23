from TcpServer import TcpServer
from TcpClient import TcpClient


class DistributedSpider(object):
    __server = TcpServer()
    __client = TcpClient()

    UnKnownRole = 0
    ServerRole = 1
    ClientRole = 2

    __role = UnKnownRole

    def __init__(self):
        super().__init__()
