import asyncio
import copy
import numpy as np
from cryptocompare import cryptocompare


def find_correlation(eth_subset, btc_data):
    """
    Находит коэффициент корреляции для периода движения цены
    ETHUSDT - eth_subset по отношению к каждому из множества ближайших периодов
    движения цены BTCUSDT - btc_data

    Для расчета используется цена закрытия периода.
    """
    step = len(eth_subset)
    eth_close_prices = [x['close'] for x in eth_subset]
    i = 0
    j = step
    for iteration in range(len(btc_data) // step):
        btc_subset = btc_data[i:j]
        btc_close_prices = [x['close'] for x in btc_subset]

        if 0 in (np.std(btc_close_prices), np.std(eth_close_prices)):
            continue

        correlation = np.corrcoef(
            eth_close_prices,
            btc_close_prices
        )[1, 0]

        if correlation > 0.2:
            return True

        i += step
        j += step


def get_subset_by_depth(data: list, base_index: int, depth: int):
    """
    Выделяет из множества движений цены ближайшие к подмножеству
    движений цены другой монеты.
    Размер возвращаемого массива задает depth
    """
    bottom_index = base_index - depth
    upper_index = base_index + depth + 1

    if bottom_index < 0:
        bottom_index = 0
    if upper_index > len(data) - 1:
        upper_index = len(data) - 1

    return data[bottom_index:upper_index]


def append_movements(own_movements, new_subset):
    if not own_movements:
        own_movements.append(new_subset)
        return

    last_movement = own_movements[-1][-1]
    if last_movement['time'] - new_subset[0]['time'] > 60:
        own_movements.append(new_subset)
    else:
        own_movements[-1] += new_subset

    return


def find_own_movements(eth_data, btc_data, step, depth):
    """
    Делит все движения цены ETHUSDT на подмножества.
    Высчитывает для каждого из них коэффицент корреляции с ближайшими
    подмножествами движения цены BTCUSDT
    """
    own_movements = []
    i = 0
    j = step
    for iteration in range(len(eth_data) // step):

        btc_subset = get_subset_by_depth(btc_data, i, depth)

        try:
            eth_subset = eth_data[i:j]
        except IndexError:
            continue

        if not find_correlation(eth_subset, copy.copy(btc_subset)):
            append_movements(own_movements, eth_subset)
        i += step
        j += step

    return own_movements


def main(limit):
    eth_candles = cryptocompare.get_historical_price_minute('ETH', currency='USDT', limit=limit)
    btc_candles = cryptocompare.get_historical_price_minute('BTC', currency='USDT', limit=limit)
    own_movements = find_own_movements(
        copy.copy(eth_candles),
        copy.copy(btc_candles),
        2,
        4
    )
    return own_movements
