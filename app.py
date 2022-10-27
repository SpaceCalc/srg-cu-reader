import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from MainWindow import MainWindow

def main() -> None:
    app = QApplication(sys.argv)

    app.setOrganizationName('NPOL517')
    app.setApplicationName('srg-cu-reader')
    app.setApplicationVersion('v1.0')

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()