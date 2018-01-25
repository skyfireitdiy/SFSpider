from sfdspider.distributedspider import DistributedSpiderClient
from PyQt5 import QtNetwork,QtCore
import sys

app = QtCore.QCoreApplication(sys.argv)
client = DistributedSpiderClient()
client.start_client(QtNetwork.QHostAddress("127.0.0.1"), 1235,
                                     QtNetwork.QHostAddress("127.0.0.1"), 1234, 4)
app.exec()