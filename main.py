import threading
import time
from abc import ABCMeta, abstractmethod
from datetime import datetime
from correlation import main


class BaseDisplay(metaclass=ABCMeta):
    """
    Абстрактный Базовый класс "наблюдателя"
    """
    def __init__(self):
        self.price_changes = []

    @abstractmethod
    def update(self, data) -> None:
        """
        Получение новых данных от наблюдаемого
        """
        pass


class BaseCoinParser(metaclass=ABCMeta):
    """
    Абстрактный Базовый класс "наблюдаемого"
    """
    @abstractmethod
    def __init__(self) -> None:
        self.observers = []

    def register(self, observer: BaseDisplay) -> None:
        self.observers.append(observer)

    def notify_display(self, data) -> None:
        for observer in self.observers:
            observer.update(data)

    @abstractmethod
    def parse(self):
        pass


class CorrelationParser(BaseCoinParser):
    def __init__(self, observer: BaseDisplay):
        self.display = observer

    def register(self, observer: BaseDisplay):
        self.display = observer

    def notify_display(self, data):
        """
        Создаем поток для обновления и вывода данных в дисплее
        и продолжаем парсить.
        :param data: новые данные для дисплея
        :return:
        """
        output_t = threading.Thread(target=self.display.update, args=(data,))
        output_t.start()
        time.sleep(0.01)

    def parse(self):
        """
        Получаем собственные движения от модуля
        из задания 1.
        Функция get_price_changes() выдаст
        только те из них, которые мы еще не сохраняли
        в дисплее и те, амплитуда которых выше или равна 1%.
        """
        movements = self.get_price_changes()
        if not movements:
            return
        for movement_subset in movements:
            # переводим данные в удобный для дисплея формат
            data = self.get_movement_data(movement_subset)
            self.notify_display(data)

    def get_price_changes(self):
        own_movements = main(60)
        if not own_movements:
            return
        own_movements = self.validate_changes(own_movements)
        return own_movements

    def validate_changes(self, movements):
        unique_movements = []
        for movements_subset in movements:
            if self.in_display(movements_subset):
                continue
            # цена открытия периода и цена его закрытия
            open_price = movements_subset[0]['open']
            close_price = movements_subset[-1]['close']

            percent = self.get_percent(close_price, open_price)
            movements_subset.append(percent)

            if abs(percent) >= 1:
                unique_movements.append(movements_subset)
        return unique_movements

    def get_movement_data(self, movements_subset):
        percent = movements_subset.pop()
        time_data = self.get_time_data(movements_subset)
        text_template = 'Собственное изменение цены на {}% c {} по {}'
        if percent in (1, -1):
            text_template = '! ' + text_template + ' !'
        notification = text_template.format(percent, time_data['start'], time_data['end'])
        data = {
            'notification': notification,
            'percent': percent,
            'movements': movements_subset,
            'display': True
        }
        return data

    @staticmethod
    def get_time_data(movement_subset):
        unix_start = int(movement_subset[0]['time'])
        unix_end = int(movement_subset[-1]['time'])

        time_data = {
            'start': datetime.utcfromtimestamp(
                unix_start
            ).strftime('%H:%M:%S'),

            'end': datetime.utcfromtimestamp(
                unix_end
            ).strftime('%H:%M:%S')
        }

        return time_data

    @staticmethod
    def get_percent(close, _open):
        if close > _open:
            result = (close - _open) / _open * 100
        else:
            result = (_open - close) / _open * 100
            result = result * -1
        return round(result, 2)

    def in_display(self, new_data):
        for data in self.display.price_changes:
            if data['movements'][0]['time'] == new_data[0]['time']:
                return True


class CorrelationDisplay(BaseDisplay):
    def update(self, data):
        self.price_changes.append(data)
        for data in self.price_changes:
            if data['display']:
                data['display'] = False
                print(data['notification'])


if __name__ == '__main__':
    display = CorrelationDisplay()
    parser = CorrelationParser(display)
    print('Поиск собственных изменений цены на 1% и более')
    while True:
        parser.parse()
