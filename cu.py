import struct
from datetime import datetime
from dataclasses import dataclass
import typing
import io


class SrgCuFile:
    """ Файл ЦУ Спектр-РГ. """

    @dataclass
    class Record:
        """ Одна запись ЦУ. """
        time:datetime   # Время МДВ.
        # Целеуказания.
        az:float        # Азимут, гр.
        el:float        # Угол места, гр.
        # Прогноз запроса.
        req_span:float  # Время распространения сигнала до КА, сек.
        req_dis:float   # Дальность, м.
        req_vel:float   # Скорость, м/с.
        req_acc:float   # Ускорение, м/с2.
        req_nd1i:int    # Код смещения частоты ПН 1.2 МГц (Nd1i).
        req_nd2i:int    # Код перестройки частоты ПН 1.2 МГц (Nd2i).
        req_n2i:int     # Код отстройки ч-ты несущей запросного сигнала (N2i).
        req_n3i:int     # Код перестройки ч-ты несущей запросного сигнала (N3i).
        # Прогноз ответа.
        res_del:float   # Полная задержка распространения сигнала, сек.
        res_dis:float   # Дальность, м.
        res_vel:float   # Скорость, м/с.
        res_acc:float   # Ускорение, м/с2.
        res_n2rj:int    # Код отстройки частоты НЕС (N2rj).
        res_n3rj:int    # Код перестройки частоты НЕС (N3rj).


    def __init__(self, file_path:typing.Union[str, None] = None) -> None:
        self.nip:int = None        # Номер НИПа.
        self.spacecraft:int = None # Номер КА.
        self.seans:int = None      # Номер сеанса.
        self.begin:datetime = None # Дата и время начала сеанса (МДВ).
        self.end:datetime = None   # Дата и время окончания сеанса (МДВ).
        self.ns:int = None         # Литера частоты запросного сигнала (Ns).
        self.ng1:int = None        # Литера частоты гетеродина конвертора (Ng1).
        self.records:typing.Tuple[SrgCuFile.Record] = () # Записи ЦУ.

        if file_path != None:
            self.read(file_path)


    def _systemtime(self, buffer_16:bytes) -> datetime:
        """ Распаковать SYSTEMTIME в datetime. """
        assert(len(buffer_16) == 16)
        dt = struct.unpack('hhhhhhhh', buffer_16)
        return datetime(dt[0], dt[1], dt[3], dt[4], dt[5], dt[6], dt[7] // 1000)

    
    def _record(self, buffer_144:bytes) -> 'SrgCuFile.Record':
        """ Распаковать структуру RECORD в класс SrgCuFile.Record. """
        assert(len(buffer_144) == 144)
        time = self._systemtime(buffer_144[:16])
        data = struct.unpack('ddddddqqqqddddqq', buffer_144[16:])
        return SrgCuFile.Record(time, *data)


    def nip_short_name(nip:int) -> typing.Union[str, None]:
        if nip == 12512: return 'MOSX'
        if nip == 12612: return 'BSX'
        if nip == 12970: return 'EVP'
        if nip == 32270: return 'USS'
        if nip == 12464: return 'MO'
        if nip == 32370: return 'EVP'
        return None
    

    def spacecraft_name(spacecraft:int) -> typing.Union[str, None]:
        if spacecraft == 720: return 'Спектр-РГ'
        return None


    def read(self, file_path:str):
        """ Прочитать бинарный файл ЦУ. """
        try:
            with open(file_path, 'rb') as file:
                self.nip, = struct.unpack('q', file.read(8))
                self.spacecraft, = struct.unpack('q', file.read(8))
                self.seans, = struct.unpack('q', file.read(8))
                file.read(8) # Резерв
                self.begin = self._systemtime(file.read(16))
                self.end = self._systemtime(file.read(16))
                self.ns, = struct.unpack('q', file.read(8))
                self.ng1, = struct.unpack('q', file.read(8))
                file.read(16) # Резерв.
                records = []
                for chunk in iter(lambda: file.read(144), b''):
                    records.append(self._record(chunk))
                self.records = tuple(records)
        except Exception as e:
            self.__init__()
            raise e


    def empty(self) -> bool:
        if self.nip != None: return False
        if self.spacecraft != None: return False
        if self.seans != None: return False
        if self.begin != None: return False
        if self.end != None: return False
        if self.ns != None: return False
        if self.ng1 != None: return False
        if len(self.records) > 0: return False
        return True


    def valid(self) -> typing.Tuple[bool, typing.Union[str, None]]:
        err = lambda x: (False, x)
        if self.empty():            return err('Объект не инициализирован')
        if self.nip == None:        return err('Нет номера пункта')
        if self.spacecraft == None: return err('Нет номера аппарата')
        if self.seans == None:      return err('Нет номера сеанса')
        if self.begin == None:      return err('Нет даты начала')
        if self.end == None:        return err('Нет даты окончания')
        if self.ns == None:         return err('Нет литеры частоты запросного сигнала (Ns)')
        if self.ng1 == None:        return err('Нет литеры частоты гетеродина конвертора (Ng1)')
        if len(self.records) == 0:  return err('Нет записей ЦУ')

        err = lambda n, v, i : (False, f'{n} {v} (запись {i+1})')
        for i, r in enumerate(self.records):
            if r.az < 0 or r.az > 360: return err('Азимут', r.az, i)
            if r.el < 0 or r.el > 90:  return err('Угол места', r.el, i)
            if r.req_span <= 0: return err('Время распространения сигнала до КА (запрос)', r.req_span, i)
            if r.req_dis  <= 0: return err('Дальность (запрос)', r.req_dis, i)
            if r.req_vel  == 0: return err('Скорость (запрос)', r.req_vel, i)
            if r.req_acc  <= 0: return err('Ускорение (запрос)', r.req_acc, i)
            if r.req_nd1i < -2**15 or r.req_nd1i > 2**15-1: return err('Код смещения частоты ПН 1.2 МГц (Nd1i) (запрос)', r.req_nd1i, i)
            if r.req_nd2i < -2**15 or r.req_nd2i > 2**15-1: return err('Код перестройки частоты ПН 1.2 МГц (Nd2i) (запрос)', r.req_nd2i, i)
            # TODO r.req_n2i
            if r.req_n3i < -2**17 or r.req_n3i > 2**17-1: return err('Код перестройки частоты несущей запросного сигнала (N3i) (запрос)', r.req_n3i, i)
            if r.res_del <= 0: return err('Полная задержка распространения сигнала (ответ)', r.res_del, i)
            if r.res_dis <= 0: return err('Дальность (ответ)', r.res_dis, i)
            if r.res_vel == 0: return err('Скорость (ответ)', r.res_vel, i)
            if r.res_acc <= 0: return err('Ускорение (ответ)', r.res_acc, i)
            # TODO r.req_n2rj
            if r.res_n3rj < -2**17 or r.res_n3rj > 2**17-1: return err('Код перестройки частоты НЕС (N3rj) (ответ)', r.res_n3rj, i)

        return True, None


    def write_txt_with(self, out):
        """ Записать текстовый файл в поток out. """

        tfmt = '%Y-%m-%d %H:%M:%S'
        out.write(f'NIP   {self.nip}\n')
        out.write(f'SC    {self.spacecraft}\n')
        out.write(f'Seans {self.seans}\n')
        out.write(f'Begin {self.begin.strftime(tfmt)}\n')
        out.write(f'End   {self.end.strftime(tfmt)}\n')
        out.write(f'Ns    {self.ns}\n')
        out.write(f'Ng1   {self.ng1}\n')
        out.write('\n')
        out.write(
            '{:5} {:19} {:7} {:6} {:5} {:17} {:11} {:8} {:6} {:6} '
            '{:7} {:7} {:5} {:17} {:11} {:8} {:7} {:7}\n'.format(
            '№', 'time', 'az', 'el', 't_sc', 'r', 'v', 'a', 'Nd1i',
            'Nd2i', 'N2i', 'N3i', 't_del', 'r', 'v', 'a', 'N2rj', 'N3rj'
        ))
        for i, r in enumerate(self.records):
            out.write(f'{i+1:<5d} ')
            out.write(f'{r.time.strftime(tfmt)} ')
            out.write(f'{r.az:7.3f} {r.el:6.3f} ')
            out.write(f'{r.req_span:5.3f} ')
            out.write(f'{r.req_dis:17.6f} ')
            out.write(f'{r.req_vel:-11.6f} ')
            out.write(f'{r.req_acc:8.6f} ')
            out.write(f'{r.req_nd1i:-6d} ')
            out.write(f'{r.req_nd2i:-6d} ')
            out.write(f'{r.req_n2i:-7d} ')
            out.write(f'{r.req_n3i:-7d} ')
            out.write(f'{r.res_del:5.3f} ')
            out.write(f'{r.res_dis:17.6f} ')
            out.write(f'{r.res_vel:-11.6f} ')
            out.write(f'{r.res_acc:8.6f} ')
            out.write(f'{r.res_n2rj:-7d} ')
            out.write(f'{r.res_n3rj:-7d}\n')
            

    def write_txt(self, file_path:str):
        """ Создать и записать текстовый файл. """
        with open(file_path, 'w', encoding='utf8') as file:
            self.write_txt_with(file)


    def write_str(self) -> str:
        """ Записать текст в строку. """
        out = io.StringIO()
        self.write_txt_with(out)
        s = out.getvalue()
        out.close()
        return s
