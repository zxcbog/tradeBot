import ccxt
import pandas as pd
import torch
import torch.utils.data
import pandas_ta as ta
from sklearn.preprocessing import MinMaxScaler
from torch.utils.data import DataLoader

def get_symbol_data(symbol, start_date):
    exchange = ccxt.bybit()
    exchange.load_markets()

    start_timestamp = exchange.parse8601(start_date.__str__())

    ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1h', since=start_timestamp, limit=1000)
    if len(ohlcv) == 0 or ohlcv[-1][0] == start_timestamp:
        return None
    data = []
    for candle in ohlcv:
        data.append({
            'Timestamp': candle[0],
            'Open': candle[1],
            'High': candle[2],
            'Low': candle[3],
            'Close': candle[4],
            'Volume': candle[5]
        })
    data = pd.DataFrame(data)
    if len(data) > 0:
        data['Timestamp'] = pd.to_datetime(data['Timestamp'], unit='ms')
        data.set_index('Timestamp', inplace=True)
        data.dropna(inplace=True)
        data.reset_index(inplace=True)
        data.drop(['Volume', 'Open', 'High', 'Low'], axis=1, inplace=True)

    return data


def fetch_crypto_data(symbol, start_date, end_date):
    data = None
    while True:
        if data is None:
            data = get_symbol_data(symbol, start_date)
        else:
            new_data = get_symbol_data(symbol, str(data.Timestamp[len(data.Timestamp) - 1]))
            if new_data is None:
                break
            result = pd.concat([data, new_data], ignore_index=True, axis=0)
            data = result
        print(data.Timestamp[len(data.Timestamp) - 1])
        print(pd.to_datetime(end_date).replace(tzinfo=None))
        if data.Timestamp[len(data.Timestamp) - 1] > pd.to_datetime(end_date).replace(tzinfo=None):
            break
    return data

class TimeSeriesDataset(torch.utils.data.Dataset):
    def __init__(self, X, y, sequence_size):
        self.X = X
        self.y = y
        self.sequence_size = sequence_size

    def __len__(self):
        return len(self.X) - self.sequence_size

    def __getitem__(self, i):
        return torch.tensor(self.X[i:i+self.sequence_size], dtype=torch.float), torch.tensor(self.y[i:i+self.sequence_size], dtype=torch.float)


def SMA(x, window_size, device):
    return torch.nn.functional.conv1d(x, torch.ones((1, 1, window_size)).to(device)) / window_size


class CcxtDataProcessing:
    def __init__(self, data, history_window_size):
        self.history_window_size = history_window_size
        data_to_train = data.copy()
        data_to_train.drop("Timestamp", axis=1, inplace=True)
        data_to_train['RSI'] = ta.rsi(data.Close, length=15)
        data_to_train['EMAF'] = ta.ema(data.Close, length=20)
        data_to_train['EMAM'] = ta.ema(data.Close, length=40)
        data_to_train['EMAS'] = ta.ema(data.Close, length=60)
        data_to_train['TargetNextClose'] = data.Close.shift(-history_window_size)
        data_to_train.dropna(inplace=True)
        shifted_df_as_np = data_to_train.to_numpy()
        x_d = torch.tensor(shifted_df_as_np[:, 0:5], dtype=torch.float)
        y_d = torch.tensor(shifted_df_as_np[:, 5:6], dtype=torch.float)
        self.x_raw_data = x_d
        self.y_raw_data = y_d
        self.scaler_x_train = MinMaxScaler(feature_range=(-1, 1))
        self.scaler_x_val = MinMaxScaler(feature_range=(-1, 1))
        self.scaler_y_train = MinMaxScaler(feature_range=(-1, 1))
        self.scaler_y_val = MinMaxScaler(feature_range=(-1, 1))

    def get_loader_inference(self):
        x_scaled = self.scaler_x_train.fit_transform(self.x_raw_data)
        dataset = TimeSeriesDataset(x_scaled, x_scaled, self.history_window_size)
        loader = DataLoader(dataset, batch_size=1, shuffle=False, drop_last=False)
        return loader

    def get_loaders_train(self, train_val_ratio, batch_size):
        train_size = int(train_val_ratio * len(self.x_raw_data))
        x_train, x_val = torch.split(self.x_raw_data, train_size)
        y_train, y_val = torch.split(self.y_raw_data, train_size)
        x_train_scaled = self.scaler_x_train.fit_transform(x_train)
        y_train_scaled = self.scaler_y_train.fit_transform(y_train)
        x_val_scaled = self.scaler_x_val.fit_transform(x_val)
        y_val_scaled = self.scaler_y_val.fit_transform(y_val)
        train_dataset = TimeSeriesDataset(x_train_scaled, y_train_scaled, self.history_window_size)
        test_dataset = TimeSeriesDataset(x_val_scaled, y_val_scaled, self.history_window_size)
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, drop_last=True)
        test_loader = DataLoader(test_dataset, batch_size=1, shuffle=False)
        return train_loader, test_loader