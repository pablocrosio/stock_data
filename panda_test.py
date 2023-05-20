import pandas

from data_helper import get_historical_data

datapath = ('backtrader/datas/2006-day-001.txt')

# Simulate the header row isn't there if noheaders requested
#skiprows = 1 if args.noheaders else 0
skiprows = 0
#header = None if args.noheaders else 0
header = 0

#dataframe = pandas.read_csv(datapath,
#                            skiprows=skiprows,
#                            header=header,
#                            parse_dates=True,
#                            index_col=0)

#dataframe = get_historical_data('BTCUSD', start_date='2023-01-01')
#dataframe = get_historical_data('BTCUSD', start_date='2022-01-01', end_date='2022-12-31')
dataframe = get_historical_data('BTCUSD', start_date='2022-01-01', end_date='2022-12-31 23:59:59', interval=240)
#dataframe = get_historical_data('BTCUSD', start_date='2021-01-01', end_date='2021-12-31 23:59:59', interval=240)
#dataframe = get_historical_data('BTCUSD', start_date='2020-01-01', end_date='2020-12-31 23:59:59', interval=240)

print(dataframe)

dataframe.to_csv('out.txt')

datapath = ('out.txt')

dataframe = pandas.read_csv(datapath,
                            skiprows=skiprows,
                            header=header,
                            parse_dates=True,
                            index_col=0)

print(dataframe)
