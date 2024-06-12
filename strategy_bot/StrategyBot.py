from config import BYBITAPIKEYTEST, BYBITSECRETKEYTEST, user, passwd, dbase, host
from LSTM_MA_strategy import *
import matplotlib.pyplot as plt
import asyncio
from DatabaseIO import DatabaseIO


class StrategyBot:
    '''
    Bot that can make decisions based on strategies. By default it using Strategy based on LSTM neural net.
    '''
    def __init__(self):
        self.bots = [ccxt.bybit({
            "apiKey": BYBITAPIKEYTEST,
            "secret": BYBITSECRETKEYTEST
        })]

        self.bots[-1].set_sandbox_mode(True)
        symbol = 'BTC/USDT'
        self.balance = self.bots[-1].fetch_balance()['info']['result']['list'][0]['totalAvailableBalance']
        self.strat = LSTMStrategy(symbol)
        self.loop = asyncio.get_event_loop()
        self.database_io = DatabaseIO(user=user, password=passwd, database=dbase, host=host, loop=self.loop)

    @staticmethod
    def create_signal(symbol: str, type: str, side: str, amount: float, price: float = 0):
        '''

        :param symbol: Symbol from market
        :param type: Type of order(limit of market)
        :param side: Side of order(Buy or Sell)
        :param amount: amount of symbol for order
        :param price: price for limit order
        :return: signal
        '''
        signal = {
            'symbol': symbol,
            'type': type,
            'side': side,
            'amount': amount,
            'price': price
        }
        return signal

    def make_orders(self, sig):
        '''
        :param sig: Signal to make order
        '''
        for bot in self.bots:
            ans = bot.create_order(symbol=sig['symbol'], type=sig['type'], side=sig['side'], amount=sig['amount'], price=sig['price'])
            self.loop.run_until_complete(self.database_io.tasks_handler(
                f"INSERT INTO transactions (transaction_type, money_amount, market_id, symbol_amount) VALUES ({1 if sig['side'] == 'Buy' else -1}, {ans}, 1, {sig['amount']})"
            ))
            print(ans)

    def scan_strategy(self):
        '''
        Method for scan signals from strategies. Strategies must be in self.strat
        '''
        #1 - buy -1 - sell
        if self.balance == 0:
            raise Exception("No money on balance!")
        data = self.loop.run_until_complete(self.database_io.tasks_handler(
            "SELECT transaction_type, money_amount, symbol_amount FROM transactions WHERE transaction_id = (SELECT MAX(transaction_id) FROM transactions)"
        ))
        if len(data) > 0:
            last_action = (data[0][0], data[0][1] if data[0][0] == 1 else 0)
            amount = data[0][2]
        else:
            amount = 0
            last_action = (0, 0)
        sig_side, last_data = self.strat.generate_signal(last_action)
        current_price = last_data.x_raw_data[-1, 0]
        if sig_side is not None:
            if sig_side == "Buy":
                amount = (0.1*self.balance)/current_price
            sig = self.create_signal("BTC/USDT", "market", sig_side, amount)
            self.make_orders(sig)

bot = StrategyBot()
bot.scan_strategy()
