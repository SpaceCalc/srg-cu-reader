from dataclasses import dataclass
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import os
from typing import List
from cu import SrgCuFile
import socket
import threading


@dataclass
class TabInfo:
    """ Информация о вкладке. """
    index:int
    path:str
    editor:QPlainTextEdit


class MainWindow(QMainWindow):
    """ Главное окно. """

    def __init__(self, paths:List[str] = []):
        super().__init__()

        # Заголовок, размер окна.
        version = QApplication.applicationVersion()
        self.setWindowTitle(f'Целеуказания Спектр-РГ {version}')
        self.resize(800, 600)

        # Верхнее меню.
        fileMenu = self.menuBar().addMenu('Файл')
        fileMenu.addAction('Открыть...', self.onOpenAction,
            QKeySequence.StandardKey.Open)
        self.closeAction = fileMenu.addAction('Закрыть', self.onCloseAction,
            QKeySequence.StandardKey.Close)
        self.saveAsAction = fileMenu.addAction('Сохранить как...',
            self.onSaveAsAction, 'Ctrl+Shift+S')
        fileMenu.addSeparator()
        fileMenu.addAction('Выход', self.close)
        self.closeAction.setEnabled(False)
        self.saveAsAction.setEnabled(False)

        # Вкладки.
        self.tabs = QTabWidget()
        self.tabs.setVisible(False)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.closeTab)
        self.tabs_info:List[TabInfo] = []

        # Разрешить Drag&Drop.
        self.setAcceptDrops(True)
        
        self.setCentralWidget(self.tabs)

        # Открыть файлы.
        self.openFiles(paths)

        self.startListen()


    def addFile(self, text:str, path:str):
        """ Добавить файл. """
        # Если файл уже открыт, то обновить текст и перейти на соотв. вкладку.
        for item in self.tabs_info:
            if item.path == path:
                item.editor.setPlainText(text)
                self.tabs.setCurrentIndex(item.index)
                return

        # Создать новый текстовый редактор.
        editor = QPlainTextEdit()
        editor.setFont(QFont("Consolas", 11))
        editor.setReadOnly(True)
        editor.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse |
            Qt.TextInteractionFlag.TextSelectableByKeyboard)
        editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        editor.setPlainText(text)
        editor.setFrameStyle(QFrame.Shape.NoFrame)

        # Создать новую вкладку.
        name = os.path.basename(path)
        tab_num = self.tabs.addTab(editor, name)
        self.tabs.setCurrentIndex(tab_num)

        # Добавить путь в уже открытые пути.
        self.tabs_info.append(TabInfo(tab_num, path, editor))

        # Отобразить вкладки (по умолчанию они не видны).
        self.tabs.setVisible(True)
        self.closeAction.setEnabled(True)
        self.saveAsAction.setEnabled(True)


    def openFiles(self, paths:List[str]):
        """ Открыть файлы в приложении. """
        for path in paths:
            try:
                cu = SrgCuFile(path)
            except:
                QMessageBox.critical(self, 
                    os.path.basename(path), 'Не удалось открыть файл.')
            else:
                self.addFile(cu.write_str(), path)


    def onOpenAction(self):
        """ Открыте файла (Файл->Открыть или Ctrl+O). """
        # Прочитать кэш.
        s = QSettings()
        dir = s.value('cache.openFileNames.dir',
            QStandardPaths.writableLocation(
                QStandardPaths.StandardLocation.DesktopLocation))
        filter = s.value('cache.openFileNames.filter', 'ЦУ (*.prognoz)')

        # Открыть диалог.
        cap = 'Открытие'
        filters = 'ЦУ (*.prognoz);; Все файлы (*.*)'
        res = QFileDialog.getOpenFileNames(self, cap, dir, filters, filter)
        paths, selected_filter = res

        if not paths:
            return

        # Сохранить кэш.
        dir = os.path.dirname(paths[0])
        s.setValue('cache.openFileNames.dir', dir)
        s.setValue('cache.openFileNames.filter', selected_filter)

        self.openFiles(paths)


    def closeTab(self, index:int):
        """ Закрыть вкладку. """

        self.tabs.removeTab(index)

        for i, item in enumerate(self.tabs_info):
            if item.index == index:
                del self.tabs_info[i]
                break
        
        if self.tabs.count() == 0:
            self.closeAction.setEnabled(False)
            self.saveAsAction.setEnabled(False)
            self.tabs.setVisible(False)


    def onCloseAction(self):
        """ Закрыть вкладку (Файл->Закрыть или Ctrl+F4). """        
        self.closeTab(self.tabs.currentIndex())


    def onSaveAsAction(self):
        """ Сохранить как (Файл->Сохранить как... или Ctrl+Shift+S). """
        # Поиск данных текущей вкладки.
        index = self.tabs.currentIndex()
        item:TabInfo = None
        for x in self.tabs_info:
            if x.index == index:
                item = x
                break
        if not item:
            return
        
        # Диалог сохранения.
        cap = 'Сохранение'
        path = item.path.replace('.prognoz', '') + '.txt'
        path, selected_filter = QFileDialog.getSaveFileName(self, cap, path)
        if not path:
            return
        
        with open(path, 'w') as file:
            file.write(item.editor.toPlainText())


    def dragEnterEvent(self, a0: QDragEnterEvent) -> None:
        """ Событие при перетягивании объектов в окно. """
        if a0.mimeData().hasUrls():
            if all(x.isLocalFile() for x in a0.mimeData().urls()):
                a0.acceptProposedAction()

    
    def dropEvent(self, a0: QDropEvent) -> None:
        """ Событие при сбросе объектов в окно. """
        paths = [x.toLocalFile() for x in a0.mimeData().urls()]
        self.openFiles(paths)


    def listen(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', 13666))
            s.listen()
            conn, addr = s.accept()
            print('connected:', addr)
            with conn:
                while True:
                    data = conn.recv(1)
                    if not data:
                        break
                    count = int.from_bytes(data, 'big')
                    print('received', data, 'as', count)

                    data = conn.recv(count)
                    if not data:
                        break
                    
                    files = data.decode('utf8').split(';')
                    print('received', data, 'as', files)

                    s.close()

    def startListen(self):
        thread = threading.Thread(target=self.listen)
        thread.start()
