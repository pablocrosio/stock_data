import backtrader as bt
import myind

class Logger():
    def __init__(self, file_name='log.txt'):
        self.file_name = file_name
        self.f = open(file_name, 'w')

    def log(self, message):
        self.f.write(message + '\n')

    def __del__(self):
        self.f.close()

class Squeeze(bt.Strategy):
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
                self.log(f'self.broker.getcash() = {self.broker.getcash()}')
                self.log(f'self.broker.getvalue() = {self.broker.getvalue()}')

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
                self.log(f'self.broker.getcash() = {self.broker.getcash()}')
                self.log(f'self.broker.getvalue() = {self.broker.getvalue()}')

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
