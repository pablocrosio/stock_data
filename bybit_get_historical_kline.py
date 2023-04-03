# this code is based on get_historical_data() from python-binance module 
# https://github.com/sammchardy/python-binance
# it also requires pybybit.py available from this page 
# https://note.mu/mtkn1/n/n9ef3460e4085 
# (where pandas & websocket-client are needed) 

import time
import dateparser
import pytz
import json
import csv
import pandas as pd 
from datetime import datetime 
from dateutil.relativedelta import relativedelta


def get_historical_klines(bybit, symbol, interval, start_str, end_str=None):
    """Get Historical Klines from Bybit 

    See dateparse docs for valid start and end string formats http://dateparser.readthedocs.io/en/latest/

    If using offset strings for dates add "UTC" to date string e.g. "now UTC", "11 hours ago UTC"

    :param symbol: Name of symbol pair -- BTCUSD, ETCUSD, EOSUSD, XRPUSD 
    :type symbol: str
    :param interval: Bybit Kline interval -- 1 3 5 15 30 60 120 240 360 720 "D" "M" "W" "Y"
    :type interval: str
    :param start_str: Start date string in UTC format
    :type start_str: str
    :param end_str: optional - end date string in UTC format
    :type end_str: str

    :return: list of OHLCV values

    """

    # set parameters for kline() 
    timeframe = str(interval)
    limit    = 200
    start_ts = int(date_to_milliseconds(start_str)/1000)
    end_ts = None
    if end_str:
        end_ts = int(date_to_milliseconds(end_str)/1000)
    else: 
        end_ts = int(date_to_milliseconds('now')/1000)


    # init our list
    output_data = []

    # loop counter 
    idx = 0
    # it can be difficult to know when a symbol was listed on Binance so allow start time to be before list date
    symbol_existed = False
    while True:
        # fetch the klines from start_ts up to max 200 entries 
        temp_dict = bybit.kline(symbol=symbol, interval=timeframe, _from=start_ts, limit=limit)

        # handle the case where our start date is before the symbol pair listed on Binance
        #if not symbol_existed and len(temp_dict):
        if not symbol_existed and len(temp_dict) and not temp_dict['result'] is None and len(temp_dict['result']):
            symbol_existed = True

        if symbol_existed:
            # extract data and convert to list 
            temp_data = [list(i.values())[2:] for i in temp_dict['result']]
            # append this loops data to our output data
            output_data += temp_data

            # update our start timestamp using the last value in the array and add the interval timeframe
            # NOTE: current implementation ignores inteval of D/W/M/Y  for now 
            #start_ts = temp_data[len(temp_data) - 1][0] + interval*60
            if len(temp_data):
                if interval == 'D' or interval == 'd':
                    start_ts = temp_data[len(temp_data) - 1][0] + 86400
                elif interval == 'W' or interval == 'w':
                    last_datetime = datetime.utcfromtimestamp(temp_data[len(temp_data) - 1][0])
                    next_datetime = last_datetime + relativedelta(weeks=1)
                    start_ts =  int(date_to_milliseconds(next_datetime.strftime('%Y-%m-%d %H:%M:%S.%d'))/1000)
                elif interval == 'M' or interval == 'm':
                    last_datetime = datetime.utcfromtimestamp(temp_data[len(temp_data) - 1][0])
                    next_datetime = last_datetime + relativedelta(months=1)
                    start_ts =  int(date_to_milliseconds(next_datetime.strftime('%Y-%m-%d %H:%M:%S.%d'))/1000)
                elif interval == 'Y' or interval == 'y':
                    last_datetime = datetime.utcfromtimestamp(temp_data[len(temp_data) - 1][0])
                    next_datetime = last_datetime + relativedelta(years=1)
                    start_ts =  int(date_to_milliseconds(next_datetime.strftime('%Y-%m-%d %H:%M:%S.%d'))/1000)
                else:
                    start_ts = temp_data[len(temp_data) - 1][0] + interval*60

        else:
            # it wasn't listed yet, increment our start date
            #start_ts += timeframe
            break

        idx += 1
        # check if we received less than the required limit and exit the loop
        if len(temp_data) < limit:
            # exit the while loop
            break

        # sleep after every 3rd call to be kind to the API
        if idx % 3 == 0:
            time.sleep(0.2)

    return output_data

def get_historical_klines_pd(bybit, symbol, interval, start_str, end_str=None):
    """Get Historical Klines from Bybit 

    See dateparse docs for valid start and end string formats 
    http://dateparser.readthedocs.io/en/latest/

    If using offset strings for dates add "UTC" to date string 
    e.g. "now UTC", "11 hours ago UTC"

    :param symbol: Name of symbol pair -- BTCUSD, ETCUSD, EOSUSD, XRPUSD 
    :type symbol: str
    :param interval: Bybit Kline interval -- 1 3 5 15 30 60 120 240 360 720 "D" "M" "W" "Y"
    :type interval: str
    :param start_str: Start date string in UTC format
    :type start_str: str
    :param end_str: optional - end date string in UTC format
    :type end_str: str

    :return: list of OHLCV values

    """

    # set parameters for kline() 
    timeframe = str(interval)
    limit    = 200
    start_ts = int(date_to_milliseconds(start_str)/1000)
    end_ts = None
    if end_str:
        end_ts = int(date_to_milliseconds(end_str)/1000)
    else: 
        end_ts = int(date_to_milliseconds('now')/1000)


    # init our list
    output_data = []

    # loop counter 
    idx = 0
    # it can be difficult to know when a symbol was listed on Binance so allow start time to be before list date
    symbol_existed = False
    while True:
        # fetch the klines from start_ts up to max 200 entries 
        temp_dict = bybit.kline(symbol=symbol, interval=timeframe, _from=start_ts, limit=limit)

        # handle the case where our start date is before the symbol pair listed on Binance
        #if not symbol_existed and len(temp_dict):
        if not symbol_existed and len(temp_dict) and not temp_dict['result'] is None and len(temp_dict['result']):
            symbol_existed = True

        if symbol_existed:
            # extract data and convert to list 
            temp_data = [list(i.values())[2:] for i in temp_dict['result']]
            # append this loops data to our output data
            output_data += temp_data

            # update our start timestamp using the last value in the array and add the interval timeframe
            # NOTE: current implementation does not support inteval of D/W/M/Y
            #start_ts = temp_data[len(temp_data) - 1][0] + interval*60
            if len(temp_data):
                if interval == 'D' or interval == 'd':
                    start_ts = temp_data[len(temp_data) - 1][0] + 86400
                elif interval == 'W' or interval == 'w':
                    last_datetime = datetime.utcfromtimestamp(temp_data[len(temp_data) - 1][0])
                    next_datetime = last_datetime + relativedelta(weeks=1)
                    start_ts =  int(date_to_milliseconds(next_datetime.strftime('%Y-%m-%d %H:%M:%S.%d'))/1000)
                elif interval == 'M' or interval == 'm':
                    last_datetime = datetime.utcfromtimestamp(temp_data[len(temp_data) - 1][0])
                    next_datetime = last_datetime + relativedelta(months=1)
                    start_ts =  int(date_to_milliseconds(next_datetime.strftime('%Y-%m-%d %H:%M:%S.%d'))/1000)
                elif interval == 'Y' or interval == 'y':
                    last_datetime = datetime.utcfromtimestamp(temp_data[len(temp_data) - 1][0])
                    next_datetime = last_datetime + relativedelta(years=1)
                    start_ts =  int(date_to_milliseconds(next_datetime.strftime('%Y-%m-%d %H:%M:%S.%d'))/1000)
                else:
                    start_ts = temp_data[len(temp_data) - 1][0] + interval*60

        else:
            # it wasn't listed yet, increment our start date
            #start_ts += timeframe
            break

        idx += 1
        # check if we received less than the required limit and exit the loop
        if len(temp_data) < limit:
            # exit the while loop
            break

        # sleep after every 3rd call to be kind to the API
        if idx % 3 == 0:
            time.sleep(0.2)

    # convert to data frame 
    df = pd.DataFrame(output_data, columns=['TimeStamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'TurnOver'])
    df = df.loc[df['TimeStamp'] <= end_ts]
    #df['Date'] = [datetime.fromtimestamp(i).strftime('%Y-%m-%d %H:%M:%S.%d')[:-3] for i in df['TimeStamp']]
    _date = [datetime.utcfromtimestamp(i).strftime('%Y-%m-%d %H:%M:%S.%d')[:-3] for i in df['TimeStamp']]
    df = df.set_index(pd.DatetimeIndex(_date))

    return df

def date_to_milliseconds(date_str: str) -> int:
    """Convert UTC date to milliseconds

    If using offset strings add "UTC" to date string e.g. "now UTC", "11 hours ago UTC"

    See dateparse docs for formats http://dateparser.readthedocs.io/en/latest/

    :param date_str: date in readable format, i.e. "January 01, 2018", "11 hours ago UTC", "now UTC"
    """
    # get epoch value in UTC
    epoch: datetime = datetime.utcfromtimestamp(0).replace(tzinfo=pytz.utc)
    # parse our date string
    d: Optional[datetime] = dateparser.parse(date_str, settings={'TIMEZONE': "UTC"})
    if not d:
        raise UnknownDateFormat(date_str)

    # if the date is not timezone aware apply UTC timezone
    if d.tzinfo is None or d.tzinfo.utcoffset(d) is None:
        d = d.replace(tzinfo=pytz.utc)

    # return the difference in time
    return int((d - epoch).total_seconds() * 1000.0)
