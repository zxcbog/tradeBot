from config import BYBITAPIKEYTEST, BYBITSECRETKEYTEST
from LSTM_MA_strategy import *
import matplotlib.pyplot as plt


class StrategyBot:
    def __init__(self):
        self.bots = [ccxt.bybit({
            "apiKey": BYBITAPIKEYTEST,
            "secret": BYBITSECRETKEYTEST
        })]
        symbol = 'BTC/USDT'
        self.strat = LSTMStrategy(symbol)
        self.bots[-1].set_sandbox_mode(True)

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
            print(ans)

    def scan_strategy(self):
        sig_side = self.strat.generate_signal()

        sig = self.create_signal("BTC/USDT", "market", sig_side, 1, 321312)
        #self.make_orders(sig)

bot = StrategyBot()
bot.scan_strategy()