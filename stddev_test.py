from datetime import datetime
import pandas as pd
import backtrader as bt
import myind

class TestStrategy(bt.Strategy):
    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.stddev = bt.indicators.StdDev(period=8)
        self.lr = bt.talib.LINEARREG(timeperiod=8)

    def next(self):
        self.log(f'self.datas[0].close[0] = {self.datas[0].close[0]}')
        self.log(f'self.stddev[0] = {self.stddev[0]}')
        self.log(f'self.lr[0] = {self.lr[0]}')

cerebro = bt.Cerebro()

cerebro.addstrategy(TestStrategy)

#index = [datetime.fromisoformat('2023-01-01'), datetime.fromisoformat('2023-01-02'), datetime.fromisoformat('2023-01-03'), datetime.fromisoformat('2023-01-04')]
#df = pd.DataFrame({'open': [1, 2, 4, 6], 'high': [10, 20, 40, 60], 'low': [0.5, 1, 2, 3], 'close': [2, 4, 6, 16], 'volume': [100, 200, 300, 400]}, index=index)

datapath = ('out2.txt')
skiprows = 0
header = 0
df = pd.read_csv(datapath,
                 skiprows=skiprows,
                 header=header,
                 parse_dates=True,
                 index_col=0)

#print(df)

data = bt.feeds.PandasData(dataname=df)
cerebro.adddata(data)

cerebro.run()

#cerebro.plot()
cerebro.plot(style='candlestick', barup='green', bardown='red')
