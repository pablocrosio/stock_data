from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse

import backtrader as bt
import backtrader.feeds as btfeeds

import pandas

from data_helper import get_historical_data


class DummyInd(bt.Indicator):
    lines = ('dummyline',)

    params = (('value', 5),)

    def __init__(self):
        self.lines.dummyline = bt.Max(0.0, self.params.value)
        print(type(self.lines.dummyline))


class ATRStopLoss(bt.indicators.AverageTrueRange):
    lines = ('short_stop_loss', 'long_stop_loss')
    plotinfo = dict(subplot=False, plotlinelabels=True)
    plotlines = dict(atr=dict(_plotskip=True), short_stop_loss=dict(marker='.', ls=''), long_stop_loss=dict(marker='.', ls=''))

    params = (('multiplier', 1.4),)

    def __init__(self):
        super(ATRStopLoss, self).__init__()
        self.lines.short_stop_loss = self.data.close + self.lines.atr * self.params.multiplier
        self.lines.long_stop_loss = self.data.close - self.lines.atr * self.params.multiplier


# Create a Stratey
class TestStrategy(bt.Strategy):
    params = (
        ('maperiod', 15),
        ('stop_loss', 0.02)  # price is 2% less than the entry point
    )

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.stop_order = None
        self.buyprice = None
        self.buycomm = None

        # Add a MovingAverageSimple indicator
        self.sma = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.maperiod)

        # Indicators for the plotting show
        #bt.indicators.ExponentialMovingAverage(self.datas[0], period=25)
        #bt.indicators.WeightedMovingAverage(self.datas[0], period=25,
        #                                    subplot=True)
        #bt.indicators.StochasticSlow(self.datas[0])
        #bt.indicators.MACDHisto(self.datas[0])
        #rsi = bt.indicators.RSI(self.datas[0])
        #bt.indicators.SmoothedMovingAverage(rsi, period=10)
        #bt.indicators.ATR(self.datas[0], plot=False)
        #DummyInd()
        #bt.indicators.Momentum(self.datas[0], period=20)
        self.atr_sl = ATRStopLoss(self.datas[0], period=14, multiplier=1.5)

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

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm: %.2f, Name: %s' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm,
                          order.info.name))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
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
        #self.log('Close, %.2f' % self.dataclose[0])
        self.log('Close, %.2f' % self.dataclose[0] + ', Position ' + ('1' if self.position else '0'))

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if self.dataclose[0] > self.sma[0]:

                # BUY, BUY, BUY!!! (with all possible default parameters)
                self.log('BUY CREATE, %.2f' % self.dataclose[0])

                self.log(f'self.atr_sl.short_stop_loss[0] = {self.atr_sl.short_stop_loss[0]:.2f}, self.atr_sl.long_stop_loss[0] = {self.atr_sl.long_stop_loss[0]:.2f}')

                # Keep track of the created order to avoid a 2nd order
                #self.order = self.buy()
                self.order = self.buy(transmit=False)
                self.order.addinfo(name='normal buy')
                #stop_price = self.dataclose[0] * (1.0 - self.p.stop_loss)
                stop_price = self.atr_sl.long_stop_loss[0]
                self.log(f'Stop price = {stop_price}')
                self.stop_order = self.sell(exectype=bt.Order.Stop, price=stop_price, parent=self.order)
                self.stop_order.addinfo(name='stop sell')
        else:

            if self.dataclose[0] < self.sma[0]:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()
                self.order.addinfo(name='normal sell')
                self.cancel(self.stop_order)


def runstrat():
    args = parse_args()

    # Create a cerebro entity
    #cerebro = bt.Cerebro(stdstats=False)
    cerebro = bt.Cerebro()

    # Add a strategy
    cerebro.addstrategy(TestStrategy)

    # Get a pandas dataframe
    #datapath = ('../../datas/2006-day-001.txt')
    datapath = ('out.txt')

    # Simulate the header row isn't there if noheaders requested
    #skiprows = 1 if args.noheaders else 0
    skiprows = 0
    #header = None if args.noheaders else 0
    header = 0

    dataframe = pandas.read_csv(datapath,
                                skiprows=skiprows,
                                header=header,
                                parse_dates=True,
                                index_col=0)

    #dataframe = get_historical_data('BTCUSD', start_date='2022-01-01')

    if not args.noprint:
        print('--------------------------------------------------')
        print(dataframe)
        print('--------------------------------------------------')

    # Pass it to the backtrader datafeed and add it to the cerebro
    data = bt.feeds.PandasData(dataname=dataframe)

    cerebro.adddata(data)

    # Set our desired cash start
    cerebro.broker.setcash(100000.0)

    # Add a FixedSize sizer according to the stake
    #cerebro.addsizer(bt.sizers.FixedSize, stake=0.1)

    # Set the commission
    cerebro.broker.setcommission(commission=0.0)
    #cerebro.broker.setcommission(commission=0.0, mult=10.0)

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    cerebro.run()

    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Plot the result
    #cerebro.plot(style='bar')
    #cerebro.plot()
    cerebro.plot(style='candlestick', barup='green', bardown='red')


def parse_args():
    parser = argparse.ArgumentParser(
        description='Pandas test script')

    parser.add_argument('--noheaders', action='store_true', default=False,
                        required=False,
                        help='Do not use header rows')

    parser.add_argument('--noprint', action='store_true', default=False,
                        help='Print the dataframe')

    return parser.parse_args()


if __name__ == '__main__':
    runstrat()