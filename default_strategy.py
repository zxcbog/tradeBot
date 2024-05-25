import pytz
from datetime import datetime as dt
import pandas as pd
import yfinance as yf
import datetime
import matplotlib.pyplot as plt
import ta.momentum
import ta.utils
import ta.trend
import ta.volatility
import numpy as np
import warnings
warnings.filterwarnings("ignore")

def strided_app(a, L, S): # Window len = L, Stride len/stepsize = S
    nrows = ((a.size - L) // S) + 1
    n = a.strides[0]
    return np.lib.stride_tricks.as_strided(a, shape=(nrows, L), strides=(S * n, n))

def numpyEWMA(price, windowSize):
    weights = np.exp(np.linspace(-1., 0., windowSize))
    weights /= weights.sum()

    a2D = strided_app(price, windowSize, 1)

    returnArray = np.empty((price.shape[0]))
    returnArray.fill(np.nan)
    for index in (range(a2D.shape[0])):
        returnArray[index + windowSize-1] = np.convolve(weights, a2D[index])[windowSize - 1:-windowSize + 1]
    return np.reshape(returnArray, (-1, 1))


def get_signals_EWMA(ewma1, ewma2, bbands, bbands2, prices, rsi):
    #ewma1 - эксп.среднее с большим окном
    #ewma2 - эксп.среднее с меньшим окном
    signals = []
    current_state = 0
    last_price = 0
    for i in range(len(ewma1)):
        if current_state != 1 and ewma1[i] > ewma2[i] and bbands[i] >= prices[i] and rsi[i] <= 40:
            signals.append((1, i, ewma1.axes[0][i]))
            current_state = 1
            last_price = prices[i]
        elif last_price != 0 and last_price / prices[i] >= 1.2 or current_state != -1 and ewma1[i] < ewma2[i] and bbands2[i] <= prices[i] and rsi[i] >= 60:
            signals.append((-1, i, ewma1.axes[0][i]))
            current_state = -1
            last_price = 0
    return np.array(signals)


def draw_signals(signals, prices):
    total_capital = 1000000
    last_price = 0
    total_profit = total_capital
    count_of_sells = 0
    percent_profit = 0
    for signal in signals:
        if signal[0] == -1 and last_price > 0:
            n_actives = total_profit // last_price
            percent_profit += prices[signal[1]] / last_price - 1
            total_profit += (prices[signal[1]] - last_price) * n_actives
            count_of_sells += 1
        else:
            last_price = prices[signal[1]]
        axs[0].scatter(signal[2], prices[signal[1]], color="green" if signal[0] == 1 else "red", s=40, marker="o")
    return total_profit - total_capital, (percent_profit * 100 if count_of_sells > 0 else 0)



if __name__ == '__main__':
    tz = pytz.timezone("America/New_York")
    start = tz.localize(dt(2023, 6, 1))
    end = tz.localize(dt.today())
    high_window = 30
    low_window = high_window // 2
    ticker = "GOOGL"
    tickers = ["RBLX", "WM", "CNI", "GOOGL", "AAPL", "TSLA", "KO", "T", "PEG", "CEG", "SPGP", "BE"]
    percents = []
    for ticker in tickers:
        ticker_df = yf.download(start=start, end=end, tickers=ticker, auto_adjust=True)
        rsi = np.array(ta.momentum.RSIIndicator(ticker_df['Close'], window=7, fillna=True).rsi())
        ticker_df['EWMA_long'] = ta.utils._ema(ticker_df['Close'] * 91.37, high_window)
        ticker_df['EWMA_short'] = ta.utils._ema(ticker_df['Close'] * 91.37, low_window)
        ticker_df['BBAND_high'] = ta.volatility.bollinger_hband(ticker_df['Close'] * 91.37, low_window + (high_window - low_window) // 2)
        ticker_df['BBAND_low'] = ta.volatility.bollinger_lband(ticker_df['Close'] * 91.37, low_window + (high_window - low_window) // 2)
        signals = get_signals_EWMA(ewma1=ticker_df['EWMA_long'], ewma2=ticker_df['EWMA_short'], bbands=ticker_df['BBAND_low'], bbands2=ticker_df['BBAND_high'], prices=ticker_df['Close'] * 91.37, rsi=rsi)
        fig, axs = plt.subplots(nrows=2, ncols=1)
        axs[0].set_title(f'{ticker} EMA{high_window}/{low_window}')
        axs[1].set_title(f'RSI{high_window}')
        total_profit, percent_profit = draw_signals(signals, ticker_df['Close'] * 91.37)
        percents.append(percent_profit)
        print(f"{ticker} profit: {total_profit:.3f} {percent_profit:.3f}%")
        axs[1].plot(rsi)
        axs[0].plot(ticker_df['EWMA_long'])
        #plt.plot(ticker_df['BBAND_high'])
        #plt.plot(ticker_df['BBAND_low'])
        axs[0].plot(ticker_df['EWMA_short'])
        axs[0].plot(ticker_df['Close'] * 91.37)
        plt.show()
    print(f"avg profit: {(sum(percents) / len(percents)):.3f}%")
    dta = 312