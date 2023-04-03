from datetime import datetime
import pandas as pd
import backtrader as bt
import myind

class AvgInd(bt.Indicator):
    lines = ('avgline',)

    params = (('cls_ind1', bt.Indicator), ('ind1_value', 5), ('cls_ind2', bt.Indicator), ('ind2_value', 5),)

    def __init__(self):
        self.ind1 = self.p.cls_ind1(value=self.p.ind1_value)
        self.ind2 = self.p.cls_ind2(value=self.p.ind2_value)

    def once(self, start, end):
        avg_array = self.lines.avgline.array
        ind1_array = self.ind1.lines.dummyline.array
        ind2_array = self.ind2.lines.dummyline.array

        for i in range(start, end):
            avg_array[i] = (ind1_array[i] + ind2_array[i]) / 2

class AvgInd2(bt.Indicator):
    lines = ('avgline',)

    params = (('indicators', []),)

    def __init__(self):
        self.indicators = self.p.indicators

    def once(self, start, end):
        if len(self.indicators) > 0:
            avg_array = self.lines.avgline.array
            for i in range(start, end):
                sum = 0
                for ind in self.indicators:
                    sum += ind.array[i]
                avg_array[i] = sum / len(self.indicators)

class DummyInd(bt.Indicator):
    lines = ('dummyline',)

    params = (('value', 5),)

    def __init__(self):
        self.lines.dummyline = bt.Max(0.0, self.params.value)
        #print(type(self.lines.dummyline))

class TestStrategy(bt.Strategy):
    params = (
        ('stop_loss', 0.02),
        ('take_profit', 0.05),
        ('risk_per_trade', 0.01),
    )

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.stop_order = None
        self.buysize = None

        #self.avg = AvgInd(cls_ind1=DummyInd, cls_ind2=DummyInd, ind2_value=8)
        #self.highest = bt.indicators.Highest(period=2)
        #self.lowest = bt.indicators.Lowest(period=2)
        #self.flag = bt.And(self.avg > self.highest, self.lowest < 5)
        #self.flag2 = bt.Or(self.flag == 1, self.flag == 1)
        #self.r = self.flag * 3 + self.flag2 * 2
        #self.avg2 = AvgInd2(indicators=[DummyInd(), DummyInd(value=8)])
        #self.sma = bt.indicators.SMA(period=2)
        #self.avg2 = AvgInd2(indicators=[DummyInd(), self.sma])
        #self.r2 = self.data.close - self.avg2
        #self.lr = bt.talib.LINEARREG(self.r2, timeperiod=2)
        #self.lr2 = bt.talib.LINEARREG(self.data.close, timeperiod=2)
        #self.tr = bt.indicators.TR()
        self.atr_sl = myind.ATRStopLoss(self.datas[0], period=14, multiplier=1.5)
        self.sqz = myind.SqueezeMomentumIndicator()

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            self.log(f'Order {order.Status[order.status]}. Name = {order.info.name}')
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm: %.2f, Name: %s' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm,
                     order.info.name))
                self.log(f'self.position = ' + ('1' if self.position else '0'))
                self.log(f'cerebro.broker.getcash() = {cerebro.broker.getcash()}')
                self.log(f'cerebro.broker.getvalue() = {cerebro.broker.getvalue()}')

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm: %.2f, Name: %s' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm,
                          order.info.name))
                self.log(f'self.position = ' + ('1' if self.position else '0'))
                self.log(f'cerebro.broker.getcash() = {cerebro.broker.getcash()}')
                self.log(f'cerebro.broker.getvalue() = {cerebro.broker.getvalue()}')

        #elif order.status in [order.Canceled, order.Margin, order.Rejected]:
        else:
            #self.log('Order Canceled/Margin/Rejected')
            self.log(f'Order {order.Status[order.status]}. Name = {order.info.name}')

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        if self.datas[0].datetime.date(0).isoformat() == '2022-03-20':
            self.log('BUY CREATE, %.2f' % self.datas[0].close[0])
            stop_price = self.atr_sl.long_stop_loss[0]
            self.buysize = self.calculate_position_size(stop_price=stop_price)
            self.log(f'order size = {self.buysize}')
            #self.order = self.buy(size=self.buysize, transmit=False)
            self.order = self.buy(size=self.buysize)
            self.order.addinfo(name='normal buy')
            # Stop loss order
            #self.stop_order = self.sell(exectype=bt.Order.Stop, price=self.data.close[0] * (1 - self.params.stop_loss), parent=self.order, size=self.buysize)
            #self.stop_order = self.sell(exectype=bt.Order.Stop, price=stop_price, parent=self.order, size=self.buysize)
            #self.stop_order.addinfo(name='stop sell')
            #self.log(f'stop price = {stop_price}')
        #if self.datas[0].datetime.date(0).isoformat() == '2022-03-30':
            #self.cancel(self.stop_order)
            #self.log('SELL CREATE, %.2f' % self.datas[0].close[0])
            #self.order = self.sell(size=0.5)
            #self.order = self.sell(size=self.buysize)
            #self.order.addinfo(name='normal sell')
            #self.stop_order = self.sell(exectype=bt.Order.Stop, price=self.buyprice, size=0.5)
            #self.stop_order.addinfo(name='stop sell')
        #self.log(len(self))
        self.log(f'self.datas[0].close[0] = {self.datas[0].close[0]:.2f}')
        #self.log(f'self.sqz[0] = {self.sqz[0]:.2f}')
        #self.log(f'self.avg.ind1.dummyline[0] = {self.avg.ind1.dummyline[0]}')
        #self.log(f'self.avg.ind2.dummyline[0] = {self.avg.ind2.dummyline[0]}')
        #self.log(f'self.avg.avgline[0] = {self.avg.avgline[0]}')
        #self.log(f'self.highest[0] = {self.highest[0]}')
        #self.log(f'self.lowest[0] = {self.lowest[0]}')
        #self.log(f'self.flag[0] = {self.flag[0]}')
        #self.log(f'self.flag2[0] = {self.flag2[0]}')
        #self.log(f'self.r[0] = {self.r[0]}')
        #self.log(f'self.sma[0] = {self.sma[0]}')
        #self.log(f'self.avg2.avgline[0] = {self.avg2.avgline[0]}')
        #self.log(f'self.r2[0] = {self.r2[0]}')
        #self.log(f'self.lr[0] = {self.lr[0]}')
        #self.log(f'self.lr2[0] = {self.lr2[0]}')
        #self.log(f'self.datas[0].high[0], self.datas[0].low[0], self.tr[0] = {self.datas[0].high[0]}, {self.datas[0].low[0]}, {self.tr[0]}')

    def calculate_position_size(self, stop_price):
        leverage = self.broker.getcommissioninfo(self.data).get_leverage()
        #risk_amount = self.broker.get_cash() * leverage * self.params.risk_per_trade
        risk_amount = 10
        #risk_amount = self.broker.get_cash() * self.params.risk_per_trade
        #stop_loss_amount = self.params.stop_loss * self.data.close[0]
        stop_loss_amount = abs(self.data.close[0] - stop_price)
        #Position size = (Account size x Percent risk) / (stop loss distance x price per share or contract)
        position_size = risk_amount / stop_loss_amount
        return position_size

cerebro = bt.Cerebro()

cerebro.addstrategy(TestStrategy)

#index = [datetime.fromisoformat('2023-01-01'), datetime.fromisoformat('2023-01-02'), datetime.fromisoformat('2023-01-03'), datetime.fromisoformat('2023-01-04')]
#df = pd.DataFrame({'open': [1, 2, 4, 6], 'high': [10, 20, 40, 60], 'low': [0.5, 1, 2, 3], 'close': [2, 4, 6, 16], 'volume': [100, 200, 300, 400]}, index=index)

datapath = ('out.txt')
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

# Set our desired cash start
#cerebro.broker.setcash(100000.0)
cerebro.broker.setcash(1000.0)

cerebro.broker.set_shortcash(False)

# Set the commission
#cerebro.broker.setcommission(commission=0.0, mult=2.0)
#cerebro.broker.setcommission(leverage=10.0)

# Print out the starting conditions
print('Starting Portfolio Cash: %.2f' % cerebro.broker.getcash())
print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

cerebro.run()

# Print out the final result
print('Final Portfolio Cash: %.2f' % cerebro.broker.getcash())
print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

#cerebro.plot()
cerebro.plot(style='candlestick', barup='green', bardown='red')
