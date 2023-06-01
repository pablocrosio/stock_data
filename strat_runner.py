import argparse
from datetime import datetime
import pandas as pd
import backtrader as bt
import backtrader.analyzers as btanalyzers
import dateparser
import data_helper

def runstrat(args=None):
    args = parse_args(args)

    cerebro = bt.Cerebro()

    stratmodule = __import__(args.stratclass.lower())
    stratclass = eval('stratmodule.' + args.stratclass)
    cerebro.addstrategy(stratclass)

    #datapath = ('out.txt')
    #skiprows = 0
    #header = 0
    #df = pd.read_csv(datapath,
    #                 skiprows=skiprows,
    #                 header=header,
    #                 parse_dates=True,
    #                 index_col=0)

    if args.fromdate == '':
        args.fromdate = '2020-07-01'

    if args.todate == '':
        args.todate = '2021-06-30 23:59:59'

    if args.interval != 'D':
        args.interval = int(args.interval)

    delta = dateparser.parse(args.todate) - dateparser.parse(args.fromdate)
    if args.interval != 'D':
        bars = delta.total_seconds() / 60 / args.interval
    else:
        bars = delta.days
    if bars > 2200:
        print('Too much bars. Maximum 2200')
        return

    df = data_helper.get_historical_data('BTCUSD', args.fromdate, args.todate, args.interval)

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

    results[0].analyzers[0].print()

    #cerebro.plot()
    cerebro.plot(style='candlestick', barup='green', bardown='red')

def parse_args(pargs=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=(
            'Strategy runner'
        )
    )

    # Strategy class to use
    parser.add_argument('--stratclass', required=False, default='Squeeze',
                        help='Strategy class to use')

    # Defaults for dates
    parser.add_argument('--fromdate', required=False, default='',
                        help='Date[time] in YYYY-MM-DD[THH:MM:SS] format')

    parser.add_argument('--todate', required=False, default='',
                        help='Date[time] in YYYY-MM-DD[THH:MM:SS] format')

    parser.add_argument('--interval', required=False, default='240',
                        help='Interval to use [D, 720, 360, 240, 120, 60]')

    parser.add_argument('--strat', required=False, default='',
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--plot', required=False, default='',
                        nargs='?', const='{}',
                        metavar='kwargs', help='kwargs in key=value format')

    return parser.parse_args(pargs)

if __name__ == '__main__':
    runstrat()
