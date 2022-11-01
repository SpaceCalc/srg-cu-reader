import struct
from datetime import datetime
from dataclasses import dataclass
import typing
import os


class SrgItnpFile:
    """ Файл ИТНП Спектр-РГ. """

    @dataclass
    class Record:
        """ Запись ИТНП. """
        time:datetime # Время в шкале МДВ.
        di:int        # Отсчёт дальности.
        nd1i:int      # Код текущей отстройки частоты ПН 1.2 МГц (Nd1i).
        nd2i:int      # Код текущей перестройки частоты ПН 1.2 МГц (Nd2i).
        nsk:int       # Отсчёт скорости (Nsk).
        dn2ri:int     # Код текущей отстройки частоты НЕС (dN2ri).
        n3ri:int      # Код текущей перестройки частоты НЕС (N3ri).
        of3:int       # Код текущей отстройки частоты Fз (синтезатор 140 МГц).
        pf3:int       # Код текущей перестройки Fз (синтезатор 140 Мгц).
        rat:float     # Отношение Рс/Рш, дБ.
        pol:int       # Полоса измерителя Рс/Рш, Гц.
        ddst:bool     # Достоверность дальности.
        dvel:bool     # Достоверность скорости.
        tmp:float     # Температура, °C.
        prs:float     # Давление, мм рт. ст.
        hmd:float     # Влажность, %.


    def __init__(self, file_path:typing.Union[str, None] = None) -> None:
        self.nip:int = None        # Номер НИПа.
        self.spacecraft:int = None # Номер КА.
        self.seans:int = None      # Номер сеанса.
        self.begin:datetime = None # Дата и время начала сеанса (МДВ).
        self.end:datetime = None   # Дата и время окончания сеанса (МДВ).
        self.ns:int = None         # Литера частоты запросного сигнала (Ns).
        self.ng1:int = None        # Литера частоты гетеродина конвектора (Ng1).
        self.delay:int = None      # Задержка комплекса в отсчётных единицах.
        self.records:typing.Tuple[SrgItnpFile.Record] = () # Записи ИТНП.

        if file_path != None:
            self.read(file_path)


    def _systemtime(self, buffer_16:bytes) -> datetime:
        """ Распаковать SYSTEMTIME в datetime."""
        assert(len(buffer_16) == 16)
        dt = struct.unpack('hhhhhhhh', buffer_16)
        return datetime(dt[0], dt[1], dt[3], dt[4], dt[5], dt[6], dt[7] // 1000)


    def _record(self, buffer_136:bytes) -> 'SrgItnpFile.Record':
        """ Распаковать структуру RECORD. """
        assert(len(buffer_136) == 136)
        t = self._systemtime(buffer_136[:16])
        data = struct.unpack('qqqqqqqqdh', buffer_136[16:-46])
        dost = buffer_136[-46]
        ddst = (dost >> 0) & 1
        dvel = (dost >> 1) & 1
        tmp, prs, hmd = struct.unpack('ddd', buffer_136[-24:])
        return SrgItnpFile.Record(t, *data, tmp, ddst, dvel, prs, hmd)


    def read(self, file_path:str) -> None:
        """ Прочитать бинарный файл ИТНП. """
        try:
            with open(file_path, 'rb') as file:
                self.nip, = struct.unpack('q', file.read(8))
                self.spacecraft, = struct.unpack('q', file.read(8))
                self.seans, = struct.unpack('q', file.read(8))
                file.read(8) # Резерв.
                self.begin = self._systemtime(file.read(16))
                self.end = self._systemtime(file.read(16))
                self.ns, = struct.unpack('q', file.read(8))
                self.ng1, = struct.unpack('q', file.read(8))
                file.read(8) # Резерв.
                self.delay = struct.unpack('q', file.read(8))[0]
                records = []
                for chunk in iter(lambda: file.read(136), b''):
                    records.append(self._record(chunk))
                self.records = tuple(records)
        except Exception as e:
            self.__init__()
            raise e


def read_all() -> None:
    root_dir = 'C:/Users/vetru/Desktop/reader-data/ITNP'
    subdirs = ['BSX', 'CORTEX', 'EVP', 'MO', 'MOSX', 'USS']
    for subdir in subdirs:
        dir_path = os.path.join(root_dir, subdir)
        for name in os.listdir(dir_path):
            print(os.path.join(subdir, name), end=' ')
            file_path = os.path.join(dir_path, name)
            try:
                itnp = SrgItnpFile(file_path)
                print('ok')
            except:
                print('error')


def main() -> None:
    # file_path = 'C:/Users/vetru/Desktop/reader-data/ITNP/MO/20220903.210034k1.NIPN-124_64.KA-720.S-409031907.W-220903.FILETYPE-7.NRKO-1.fgitnp'
    file_path = 'C:/Users/vetru/Desktop/reader-data/ITNP/USS/20220913.204010k2.NIPN-322_70.KA-720.S-409131756.W-220913.FILETYPE-8.NRKO-1.fgitnp'
    itnp = SrgItnpFile(file_path)


if __name__ == '__main__':
    main()