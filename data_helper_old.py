from datetime import datetime
#import yfinance as yf
from datetime import timedelta
import math
from pybybit import Bybit
from bybit_get_historical_kline import get_historical_klines_pd
from dateutil.relativedelta import relativedelta

#def get_historical_data(ticker, start_date, end_date=datetime.today().strftime('%Y-%m-%d'), interval='1d'):
#    yfobj = yf.Ticker(ticker)
#    data = yfobj.history(start=start_date, end=end_date, interval=interval)
#    return data

def get_historical_data(ticker, start_date, end_date=datetime.today().strftime('%Y-%m-%d'), interval='D'):
    bybit = Bybit(api_key='xxxxxxxxx', secret='yyyyyyyyyyyyyyyyyyy', symbol='BTCUSD', test=False, ws=False)
    data = get_historical_klines_pd(bybit, ticker, interval, start_str=start_date, end_str=end_date)

    data['Open'] = data['Open'].astype(float)
    data['High'] = data['High'].astype(float)
    data['Low'] = data['Low'].astype(float)
    data['Close'] = data['Close'].astype(float)
    data['Volume'] = data['Volume'].astype(float)
    data['TurnOver'] = data['TurnOver'].astype(float)

    return data

#def get_data_start_date(start_date, window, interval='1d'):
#    days = _window2days(window, interval)
#    #print(f'days = {days}')
#    timedelta_to_subtract = timedelta(days=days)
#    return datetime.fromisoformat(start_date) - timedelta_to_subtract

def get_data_start_date(start_date, window, interval='D'):
    start_datetime = datetime.fromisoformat(start_date)
    if interval == 'D' or interval == 'd':
        data_start_datetime = start_datetime - timedelta(days=window)
    elif interval == 'W' or interval == 'w':
        data_start_datetime = start_datetime - relativedelta(weeks=window)
    elif interval == 'M' or interval == 'm':
        data_start_datetime = start_datetime - relativedelta(months=window)
    elif interval == 'Y' or interval == 'y':
        data_start_datetime = start_datetime - relativedelta(years=window)
    else:
        data_start_datetime = start_datetime - timedelta(minutes=interval*window)
    return data_start_datetime.strftime('%Y-%m-%d %H:%M:%S.%d')

def _window2days(window, interval):
    if (interval.endswith('m')):
        int_interval = int(interval.replace('m', ''))
        days = math.ceil((window * int_interval) / (60 * 24))
    elif (interval.endswith('h')):
        int_interval = int(interval.replace('h', ''))
        days = math.ceil((window * int_interval) / 24)
    elif (interval.endswith('d')):
        int_interval = int(interval.replace('d', ''))
        days = window * int_interval
    elif (interval.endswith('wk')):
        int_interval = int(interval.replace('wk', ''))
        days = window * int_interval * 7
    elif (interval.endswith('mo')):
        int_interval = int(interval.replace('mo', ''))
        days = window * int_interval * 30
    else: # days
        days = window
    return days

if __name__ == "__main__":
    #data = get_historical_data('BTC-USD', start_date='2022-01-01', end_date='2022-03-31')
    #data = get_historical_data('BTCUSD', start_date='2022-01-01', end_date='2022-05-01', interval=240)
    data = get_historical_data('BTCUSD', start_date='2022-01-01')
    #print(data.tail())
    print(data)
