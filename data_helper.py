from datetime import datetime
from datetime import timedelta
import dateparser
import os
import pandas as pd
from pybybit import Bybit
from bybit_get_historical_kline import get_historical_klines_pd

def get_historical_data(ticker, start_date, end_date=datetime.today().strftime('%Y-%m-%d'), interval='D'):
    if not _is_valid_interval(interval):
        raise Exception(f'Interval {interval} not implemented')
    ticker_w = ticker.lower()
    interval_w = interval.lower() if type(interval) is str else f'{interval}'
    if not os.path.isdir(ticker_w):
        os.mkdir(ticker_w)
    if not os.path.isdir(f'{ticker_w}/{interval_w}'):
        os.mkdir(f'{ticker_w}/{interval_w}')
    start_date_w = start_date
    data_w = None
    end = False
    while not end:
        start_offset, end_offset = _get_offsets(start_date_w, interval)
        file_name = start_offset.replace('-', '_') + '.txt'
        data_path = f'{ticker_w}/{interval_w}/{file_name}'
        if os.path.isfile(data_path):
            data = _get_data_from_path(data_path)
            # check for updates
            if len(data.index) > 0:
                if data.index[-1] < dateparser.parse(end_offset):
                    interval_timedelta = _get_interval_timedelta(interval)
                    end_offset_timedelta = dateparser.parse(end_offset) - data.index[-1]
                    #print(f'end_offset_timedelta = {end_offset_timedelta}')
                    #print(f'interval_timedelta = {interval_timedelta}')
                    if end_offset_timedelta > interval_timedelta:
                        new_start = (data.index[-1] + _get_interval_timedelta(interval)).strftime('%Y-%m-%d %H:%M:%S')
                        #print(f'new_start = {new_start}')
                        new_data = _get_data_from_host(ticker, new_start, end_offset, interval)
                        #print(new_data)
                        data = pd.concat([data, new_data])
                        data.to_csv(data_path)
        else:
            data = _get_data_from_host(ticker, start_offset, end_offset, interval)
            data.to_csv(data_path)
        if data_w is None:
            data_w = data
        else:
            data_w = pd.concat([data_w, data])
        if dateparser.parse(end_offset) < dateparser.parse(end_date):
            start_date_w = dateparser.parse(end_offset) + _get_interval_timedelta(interval)
            start_date_w = start_date_w.strftime('%Y-%m-%d')
        else:
            end = True
    return data_w.loc[(data_w.index >= start_date) & (data_w.index <= end_date)]
    #return data_w

def _is_valid_interval(interval):
    return interval in ['D', 720, 360, 240, 120, 60]

def _get_offsets(start_date, interval='D'):
    d = dateparser.parse(start_date)
    if interval == 'D':
        start_offset = f'{d.year}-01-01'
        end_offset = f'{d.year}-12-31'
    elif interval == 720 or interval == 360 or interval == 240: # 12H, 6H, 4H
        if d.month < 7:
            start_offset = f'{d.year}-01-01'
            end_offset = f'{d.year}-06-30 23:59:59'
        else:
            start_offset = f'{d.year}-07-01'
            end_offset = f'{d.year}-12-31 23:59:59'
    elif interval == 120 or interval == 60: # 2H, 1H
        if d.month < 4:
            start_offset = f'{d.year}-01-01'
            end_offset = f'{d.year}-03-31 23:59:59'
        elif d.month < 7:
            start_offset = f'{d.year}-04-01'
            end_offset = f'{d.year}-06-30 23:59:59'
        elif d.month < 10:
            start_offset = f'{d.year}-07-01'
            end_offset = f'{d.year}-09-30 23:59:59'
        else:
            start_offset = f'{d.year}-10-01'
            end_offset = f'{d.year}-12-31 23:59:59'
    else:
        raise Exception(f'Interval {interval} not implemented')
    return start_offset, end_offset

def _get_data_from_path(data_path):
    data = pd.read_csv(data_path,
                       skiprows=0,
                       header=0,
                       parse_dates=True,
                       index_col=0)
    return data

def _get_data_from_host(ticker, start_date, end_date=datetime.today().strftime('%Y-%m-%d'), interval='D'):
    bybit = Bybit(api_key='xxxxxxxxx', secret='yyyyyyyyyyyyyyyyyyy', symbol='BTCUSD', test=False, ws=False)
    data = get_historical_klines_pd(bybit, ticker, interval, start_str=start_date, end_str=end_date)

    data['Open'] = data['Open'].astype(float)
    data['High'] = data['High'].astype(float)
    data['Low'] = data['Low'].astype(float)
    data['Close'] = data['Close'].astype(float)
    data['Volume'] = data['Volume'].astype(float)
    data['TurnOver'] = data['TurnOver'].astype(float)

    return data

def _get_interval_timedelta(interval):
    if interval == 'D':
        return timedelta(days=1)
    else: # 720, 360, 240, 120, 60
        return timedelta(minutes=interval)
