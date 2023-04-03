import backtrader as bt

class ATRStopLoss(bt.indicators.AverageTrueRange):
    lines = ('short_stop_loss', 'long_stop_loss')
    plotinfo = dict(subplot=False, plotlinelabels=True)
    plotlines = dict(atr=dict(_plotskip=True), short_stop_loss=dict(marker='.', ls=''), long_stop_loss=dict(marker='.', ls=''))

    params = (('multiplier', 1.4),)

    def __init__(self):
        super(ATRStopLoss, self).__init__()
        self.lines.short_stop_loss = self.data.close + self.lines.atr * self.params.multiplier
        self.lines.long_stop_loss = self.data.close - self.lines.atr * self.params.multiplier

class SqueezeMomentumIndicator(bt.Indicator):
    lines = ('val', 'sqz_on', 'sqz_off', 'no_sqz')

    params = (
        ('length', 20),
        ('mult', 2.0),
        ('length_kc', 20),
        ('mult_kc', 1.5),
        ('use_true_range', True),
    )

    def __init__(self):
        source = self.data.close
        self.basis = bt.indicators.SMA(source, period=self.params.length)
        self.dev = self.params.mult_kc * bt.indicators.StdDev(source, period=self.params.length)

        if self.params.use_true_range:
            #self.range = self.data.tr
            self.range = bt.indicators.TR()
        else:
            self.range = self.data.high - self.data.low

        self.ma = bt.indicators.SMA(source, period=self.params.length_kc)
        self.rangema = bt.indicators.SMA(self.range, period=self.params.length_kc)

        self.upper_bb = self.basis + self.dev
        self.lower_bb = self.basis - self.dev

        self.upper_kc = self.ma + self.rangema * self.params.mult_kc
        self.lower_kc = self.ma - self.rangema * self.params.mult_kc

        #self.sqz_on = (self.lower_bb > self.lower_kc) & (self.upper_bb < self.upper_kc)
        self.sqz_on = bt.And(self.lower_bb > self.lower_kc, self.upper_bb < self.upper_kc)
        #self.sqz_off = (self.lower_bb < self.lower_kc) & (self.upper_bb > self.upper_kc)
        self.sqz_off = bt.And(self.lower_bb < self.lower_kc, self.upper_bb > self.upper_kc)
        #self.no_sqz = ~(self.sqz_on | self.sqz_off)
        self.no_sqz = bt.And(self.sqz_on == 0, self.sqz_off == 0)

        #self.val = bt.indicators.LinearReg(
        #    source - bt.indicators.Avg(
        #        [bt.indicators.Highest(self.data.high, period=self.params.length_kc),
        #         bt.indicators.Lowest(self.data.low, period=self.params.length_kc),
        #         bt.indicators.SMA(self.data.close, period=self.params.length_kc)]
        #    ),
        #    period=self.params.length_kc,
        #)
        self.avg = (
                    (
                     bt.indicators.Highest(self.data.high, period=self.params.length_kc) +
                     bt.indicators.Lowest(self.data.low, period=self.params.length_kc)
                    ) / 2 +
                    bt.indicators.SMA(self.data.close, period=self.params.length_kc)
                   ) / 2                   
        self.val = bt.talib.LINEARREG(source - self.avg, timeperiod=self.params.length_kc)

    def next(self):
        #if self.datas[0].datetime.date(0).isoformat() == '2022-12-15':
        #    print(f'self.basis[0] = {self.basis[0]:.2f}')
        #    print(f'self.dev[0] = {self.dev[0]:.2f}')
        #    print(f'self.range[0] = {self.range[0]:.2f}')
        #    print(f'self.ma[0] = {self.ma[0]:.2f}')
        #    print(f'self.rangema[0] = {self.rangema[0]:.2f}')
        #    print(f'self.upper_bb[0] = {self.upper_bb[0]:.2f}')
        #    print(f'self.lower_bb[0] = {self.lower_bb[0]:.2f}')
        #    print(f'self.upper_kc[0] = {self.upper_kc[0]:.2f}')
        #    print(f'self.lower_kc[0] = {self.lower_kc[0]:.2f}')
        #    print(f'self.avg[0] = {self.avg[0]:.2f}')
        #    print(f'self.val[0] = {self.val[0]:.2f}')

        self.lines.val[0] = self.val[0]

        if self.sqz_on:
            self.lines.sqz_on[0] = 1.0
            self.lines.sqz_off[0] = 0.0
            self.lines.no_sqz[0] = 0.0
        elif self.sqz_off:
            self.lines.sqz_on[0] = 0.0
            self.lines.sqz_off[0] = 1.0
            self.lines.no_sqz[0] = 0.0
        else:
            self.lines.sqz_on[0] = 0.0
            self.lines.sqz_off[0] = 0.0
            self.lines.no_sqz[0] = 1.0
