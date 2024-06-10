from config import BYBITAPIKEYTEST, BYBITSECRETKEYTEST, user, passwd, dbase, host
from LSTM_MA_strategy import *
import matplotlib.pyplot as plt
import asyncio
from DatabaseIO import DatabaseIO


class StrategyBot:
    def __init__(self):
        self.bots = [ccxt.bybit({
            "apiKey": BYBITAPIKEYTEST,
            "secret": BYBITSECRETKEYTEST
        })]
        symbol = 'BTC/USDT'
        self.strat = LSTMStrategy(symbol)
        self.bots[-1].set_sandbox_mode(True)
        self.loop = asyncio.get_event_loop()
        self.database_io = DatabaseIO(user=user, password=passwd, database=dbase, host=host, loop=self.loop)

    @staticmethod
    def create_signal(symbol: str, type: str, side: str, amount: float, price: float):
        signal = {
            'symbol': symbol,
            'type': type,
            'side': side,
            'amount': amount,
            'price': price
        }
        return signal

    def make_orders(self, sig):
        for bot in self.bots:
            ans = bot.create_order(symbol=sig['symbol'], type=sig['type'], side=sig['side'], amount=sig['amount'], price=sig['price'])
            self.loop.run_until_complete(self.database_io.tasks_handler(
                f"INSERT INTO transactions (transaction_type, money_amount, market_id) VALUES ({1 if sig['side'] == 'Buy' else -1}, {ans}, 1)"
            ))
            print(ans)

    def scan_strategy(self):
        #1 - buy -1 - sell
        data = self.loop.run_until_complete(self.database_io.tasks_handler(
            "SELECT transaction_type, money_amount FROM transactions WHERE transaction_id = (SELECT MAX(transaction_id) FROM transactions)"
        ))
        if len(data) > 0:
            last_action = (data[0][0], data[0][1] if data[0][0] == 1 else 0)
        else:
            last_action = (0, 0)
        sig_side = self.strat.generate_signal(last_action)
        if sig_side is not None:
            sig = self.create_signal("BTC/USDT", "market", sig_side, 1)
            self.make_orders(sig)

bot = StrategyBot()
bot.scan_strategy()