import copy
from cryptocompare import cryptocompare
import numpy as np


def find_correlation(eth_subset, btc_data, stop):
    """
    Делит btc_data (список движений цены BTCUSDT) на подмножества
    Равные по количеству eth_subset для установления корреляции
    между ними.

    Для расчета используется цена закрытия периода.

    :param eth_subset: подмножество движений цен ETHUSDT
    :param btc_data: полный список движений цен BTCUSDT
    :param stop: Устанавливает количество итераций по нахождению
    коэффициента корреляции между eth_subset и btc_subset'тами
    :return: True если движение цены eth_subset НЕ самостоятельное,
    None если самостоятельное
    """
    step = len(eth_subset)
    eth_close_prices = [x['close'] for x in eth_subset]

    for i in range(len(btc_data) // step):
        if i == stop:
            break

        btc_subset = btc_data[0:step]
        btc_close_prices = [x['close'] for x in btc_subset]

        if 0 in (np.std(btc_close_prices), np.std(eth_close_prices)):
            continue

        correlation = np.corrcoef(
            eth_close_prices,
            btc_close_prices
        )[1, 0]

        if correlation > 0.2:
            return True

        for element in btc_subset:
            btc_data.remove(element)


def find_own_movements(eth_data, btc_data, step):
    """
    Делит eth_data на eth_subset'ы - подмножества/периоды движения цены.
    Передает eth_subset функции find_correlation для проверки самостоятельности
    периода движения цены. Самостоятельные периоды складываются в own_movements.

    :param eth_data: Все периоды движения цены ETHUSDT
    :param btc_data: Все периоды движения цены BTCUSDT
    :param step: задает количество элементов в eth_subset
    :return: Собственные движения цены ETHUSDT в виде списка own_movements
    """
    own_movements = []
    for i in range(len(eth_data) // step):
        try:
            subset = eth_data[0:step]

            if not find_correlation(subset, btc_data, 5):
                own_movements += subset

            for element in subset:
                eth_data.remove(element)
        except IndexError:
            pass

    return own_movements


if __name__ == '__main__':
    # Получить все движения цен ETHUSDT/BTCUSDT
    eth_candles = cryptocompare.get_historical_price_minute('ETH', currency='USDT', limit=1440)
    btc_candles = cryptocompare.get_historical_price_minute('BTC', currency='USDT', limit=1440)
    # Запуск алгоритма поиска собственных движений цены ETHUSDT
    own_movements = find_own_movements(
        copy.copy(eth_candles),
        copy.copy(btc_candles),
        2
    )
    # Распечатка каждого из собственных движений
    for movement in own_movements:
        print(movement)

    print(
        '\nНайдено',
        len(own_movements),
        'самостоятельных движений цены ETHUSDT длинной в 1 минуту.'
    )
    print(
        'Поиск осуществлен по',
        len(eth_candles),
        'одноминутным движениям цены'
    )
    # Коэффициент общей корреляции ETHUSDT/BTCUSDT
    corrcoef = np.corrcoef(
        [x['close'] for x in eth_candles],
        [x['close'] for x in btc_candles]
    )[1, 0]

    print('\nКоэффициент корреляции ETHUSDT/BTCUSDT', corrcoef)
