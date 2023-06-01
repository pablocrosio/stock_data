from datetime import datetime
import pandas as pd
import backtrader as bt
import backtrader.analyzers as btanalyzers
import myind

class Logger():
    def __init__(self, file_name='log.txt'):
        self.file_name = file_name
        self.f = open(file_name, 'w')

    def log(self, message):
        self.f.write(message + '\n')

    def __del__(self):
        self.f.close()

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
        ('risk_per_trade', 0.02),
    )

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        #dt = dt or self.datas[0].datetime.date(0)
        dt = dt or self.datas[0].datetime.datetime(0)
        print('%s, %s' % (dt.isoformat(), txt))
        self.logger.log(dt.isoformat() + ', ' + txt)

    def __init__(self):
        self.logger = Logger()
        self.order = None
        self.entry_type = None
        self.entry_size = None
        self.entry_price = None
        self.entry_comm = None
        self.stop_order = None
        self.profit_order = None
        self.set_second_stop_order = None

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
        self.atr_sl2 = myind.ATRStopLoss(self.datas[0], period=14, multiplier=1)
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

                if (order.info.name == 'entry buy'):
                    self.entry_price = order.executed.price
                    self.entry_comm = order.executed.comm
                if (order.info.name == 'profit buy 1'):
                    self.set_second_stop_order = 1
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm: %.2f, Name: %s' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm,
                          order.info.name))
                self.log(f'self.position = ' + ('1' if self.position else '0'))
                self.log(f'cerebro.broker.getcash() = {cerebro.broker.getcash()}')
                self.log(f'cerebro.broker.getvalue() = {cerebro.broker.getvalue()}')

                if (order.info.name == 'entry sell'):
                    self.entry_price = order.executed.price
                    self.entry_comm = order.executed.comm
                if (order.info.name == 'profit sell 1'):
                    self.set_second_stop_order = 1

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
        # Simply log the closing price of the series from the reference
        self.log(f'self.datas[0].close[0] = {self.datas[0].close[0]:.2f}')

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if self.sqz[0] > 0 and self.sqz[0] > self.sqz[-1] and self.sqz[-1] > self.sqz[-2]:

                self.log('ENTRY BUY CREATE, %.2f' % self.datas[0].close[0])
                self.entry_type = 'buy'
                stop_price = self.atr_sl.long_stop_loss[0]
                self.entry_size = self.calculate_position_size(stop_price=stop_price)
                self.log(f'order size = {self.entry_size}')
                self.order = self.buy(size=self.entry_size, transmit=False)
                self.order.addinfo(name='entry buy')
                # Stop loss order
                self.stop_order = self.sell(exectype=bt.Order.Stop, price=stop_price, parent=self.order, size=self.entry_size, transmit=False)
                self.stop_order.addinfo(name='stop sell 1')
                self.log(f'stop price = {stop_price}')
                profit_price = self.atr_sl2.short_stop_loss[0]
                self.log(f'profit price = {profit_price}')
                self.profit_order = self.sell(exectype=bt.Order.Limit, price=profit_price, parent=self.order, size=self.entry_size * 0.5)
                self.profit_order.addinfo(name='profit sell 1')
                self.set_second_stop_order = 0

            else:

                # Not yet ... we MIGHT SELL if ...
                if self.sqz[0] < 0 and self.sqz[0] < self.sqz[-1] and self.sqz[-1] < self.sqz[-2]:

                    self.log('ENTRY SELL CREATE, %.2f' % self.datas[0].close[0])
                    self.entry_type = 'sell'
                    stop_price = self.atr_sl.short_stop_loss[0]
                    self.entry_size = self.calculate_position_size(stop_price=stop_price)
                    self.log(f'order size = {self.entry_size}')
                    self.order = self.sell(size=self.entry_size, transmit=False)
                    self.order.addinfo(name='entry sell')
                    # Stop loss order
                    self.stop_order = self.buy(exectype=bt.Order.Stop, price=stop_price, parent=self.order, size=self.entry_size, transmit=False)
                    self.stop_order.addinfo(name='stop buy 1')
                    self.log(f'stop price = {stop_price}')
                    profit_price = self.atr_sl2.long_stop_loss[0]
                    self.log(f'profit price = {profit_price}')
                    self.profit_order = self.buy(exectype=bt.Order.Limit, price=profit_price, parent=self.order, size=self.entry_size * 0.5)
                    self.profit_order.addinfo(name='profit buy 1')
                    self.set_second_stop_order = 0

        else:

            if self.entry_type == 'buy':

                if self.sqz[0] < 0:

                    #if self.stop_order.info.name == 'stop sell 1':
                    if self.stop_order.info.name == 'stop sell 1' and not self.set_second_stop_order:
                        self.log(f'***** CASO RARO *****')
                        size = self.entry_size
                    else:
                        size = self.entry_size * 0.5
                    self.log('EXIT SELL CREATE, %.2f' % self.datas[0].close[0])
                    self.order = self.sell(size=size)
                    self.order.addinfo(name='exit sell')
                    self.log(f'CANCEL STOP ORDER, {self.stop_order.info.name}, {self.stop_order.Status[self.stop_order.status]}')
                    self.cancel(self.stop_order)

                else:

                    if self.set_second_stop_order:

                        self.log('STOP SELL 2 CREATE, %.2f' % self.entry_price)
                        self.stop_order = self.sell(exectype=bt.Order.Stop, price=self.entry_price, size=self.entry_size * 0.5)
                        self.stop_order.addinfo(name='stop sell 2')
                        self.set_second_stop_order = 0

            else:

                if self.sqz[0] > 0:

                    #if self.stop_order.info.name == 'stop buy 1':
                    if self.stop_order.info.name == 'stop buy 1' and not self.set_second_stop_order:
                        self.log(f'***** CASO RARO *****')
                        size = self.entry_size
                    else:
                        size = self.entry_size * 0.5
                    self.log('EXIT BUY CREATE, %.2f' % self.datas[0].close[0])
                    self.order = self.buy(size=size)
                    self.order.addinfo(name='exit buy')
                    self.log(f'CANCEL STOP ORDER, {self.stop_order.info.name}, {self.stop_order.Status[self.stop_order.status]}')
                    self.cancel(self.stop_order)

                else:

                    if self.set_second_stop_order:

                        self.log('STOP BUY 2 CREATE, %.2f' % self.entry_price)
                        self.stop_order = self.buy(exectype=bt.Order.Stop, price=self.entry_price, size=self.entry_size * 0.5)
                        self.stop_order.addinfo(name='stop buy 2')
                        self.set_second_stop_order = 0

        #self.log(len(self))
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
        risk_amount = self.broker.get_cash() * self.params.risk_per_trade
        #risk_amount = 10
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
cerebro.broker.setcash(1000)

cerebro.broker.set_shortcash(False)

# Set the commission
#cerebro.broker.setcommission(commission=0.0, mult=2.0)
#cerebro.broker.setcommission(commission=0.0001, leverage=10.0)
cerebro.broker.setcommission(leverage=10.0)

cerebro.addanalyzer(btanalyzers.TradeAnalyzer, _name='trade_analyzer')

# Print out the starting conditions
print('Starting Portfolio Cash: %.2f' % cerebro.broker.getcash())
print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

results = cerebro.run()

# Print out the final result
print('Final Portfolio Cash: %.2f' % cerebro.broker.getcash())
print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

#results[0].analyzers[0].print()

#cerebro.plot()
cerebro.plot(style='candlestick', barup='green', bardown='red')
