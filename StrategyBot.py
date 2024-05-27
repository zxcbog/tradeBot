import BotTrader_bybit
import ccxt
from config import BYBITAPIKEY, BYBITSECRETKEY, BYBITAPIKEYTEST, BYBITSECRETKEYTEST

class StrategyBot:
    def __init__(self):
        self.bots = [ccxt.bybit({
            "apiKey": BYBITAPIKEYTEST,
            "secret": BYBITSECRETKEYTEST
        })]
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
        sig = self.create_signal("BTC/USDT", "market", "Buy", 1, 321312)
        self.make_orders(sig)

bot = StrategyBot()
bot.scan_strategy()