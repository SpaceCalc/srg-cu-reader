import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from MainWindow import MainWindow
import resources
import socket
from typing import List


def int_to_bytes(x:int) -> bytes:
    return x.to_bytes((x.bit_length() + 7) // 8, 'big')


def redirect(files:List[str]):
    msg = ';'.join(files).encode('utf8')
    msg = int_to_bytes(len(msg)) + msg
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.001)
        s.connect(('127.0.0.1', 13666))
        s.sendall(msg)


def main() -> None:

    files = sys.argv[1:]
    if files:
        redirect(files)
        exit(0)

    app = QApplication(sys.argv)

    app.setOrganizationName('NPOL517')
    app.setApplicationName('srg-cu-reader')
    app.setApplicationVersion('v1.0')
    app.setWindowIcon(QIcon(":/icons/icon.ico"))

    window = MainWindow(files)
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()