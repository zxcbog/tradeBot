import os

import pytz
from datetime import datetime as dt
import datetime
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import torch
from strategy_utils import *
from model import LSTM
from Strategy import Strategy

class LSTMStrategy(Strategy):
    def __init__(self, symbol):
        super(LSTMStrategy, self).__init__()
        self.symbol = symbol
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = LSTM(5, 32, 1, self.device).to(self.device)

    def generate_signal(self, last_action, test=False):
        '''
        postprocess signal data
        :param last_action: last action made by strategy bot
        :param test: if you need to plot results - test=True
        :return: signal side and parsed symbol data
        '''
        self.load_weights("LSTMStrategy_weights.pth")
        raw_sig, last_data = self.inference(last_action)
        if len(raw_sig) == 0:
            return None, None
        if test:
            plt.plot(last_data.x_raw_data[:, 0])
            for point in raw_sig:
                plt.plot(point[0], last_data.x_raw_data[point[0], 0], 'ro', color=point[1])
            plt.show()
        return "Buy" if raw_sig[-1][1] == "green" else "Sell", last_data

    def inference(self, last_action, down_bound=-0.03, top_bound=0.017, stop_loss=0.1, start_date=None, end_date=None, history_window_size=48):
        '''
        Function for inference generation of signal
        :param last_action: last action made by bot
        :param down_bound: lower bound for signal strategy
        :param top_bound: higher bound for signal strategy
        :param stop_loss: stop loss
        :param start_date: start date for parsing data
        :param end_date: end date for parsing data
        :param history_window_size: window size for historical analysis
        :return: generated signals and parsed data
        '''
        points = []
        if start_date is None:
            start_date = (dt.today() - datetime.timedelta(days=15)).__str__()
        if end_date is None:
            end_date = dt.today()
        last_data = CcxtDataProcessing(fetch_crypto_data(self.symbol, start_date, end_date), history_window_size)
        train_loader = last_data.get_loader_inference()
        self.model.eval()
        drsi_prev = 0
        buy_price = last_action[1]
        last_act = last_action[0]
        with torch.no_grad():
            for i, data in enumerate(train_loader):
                if i < len(train_loader) - 1:
                    continue
                x, _ = data
                x = x.to(self.device)
                output = self.model(x)
                detached_x = last_data.scaler_x_train.inverse_transform(x.clone().detach().cpu().reshape(x.shape[1], x.shape[2]))
                sma = SMA(torch.unsqueeze(x[0, :, 0], dim=0), 6, self.device)[0]
                action = None
                start_act = last_act
                drsi_n = output[0].clone().detach() - sma.clone().detach()[-1]
                drsi = 0
                if drsi_prev != 0:
                    drsi = drsi_n - drsi_prev
                drsi_prev = drsi_n
                if (output[0] - sma[-1] >= top_bound and drsi <= 1e-3):
                    action = (i + x.shape[1], "green")
                    buy_price = detached_x[-1, -1]
                    #print(f"buy price: {buy_price}")
                    #points.append(action)
                    last_act = 1
                elif (output[0] - sma[-1] <= down_bound and drsi >= -1e-4) or (buy_price != 0 and (detached_x[-1, 0] / buy_price - 1) < -stop_loss):
                    action = (i + x.shape[1], "red")
                    buy_price = 0
                    #print(f"sell price: {detached_x[-1, 0]}")
                    #points.append(action)
                    last_act = -1
                if start_act != last_act:
                    if action[1] == "green":
                        buy_price = detached_x[-1, -1]
                        print(f"buy price: {buy_price}")
                    else:
                        print(f"sell price: {detached_x[-1, -1]}")
                        buy_price = 0
                    points.append(action)
            return points, last_data

    def load_weights(self, weights_path):
        self.model.load_state_dict(torch.load(weights_path))

    @staticmethod
    def prepare_data_to_train(symbol, start_date, end_date, history_window_size):
        if "csv_data.csv" not in os.listdir():
            data = fetch_crypto_data(symbol, start_date, end_date)
            data.to_csv("csv_data.csv", encoding='utf-8')
        else:
            data = pd.read_csv("csv_data.csv")
        return CcxtDataProcessing(data, history_window_size)

    def train(self, train_epochs, start_date, end_date, batch_size, history_window_size, val_ratio):
        '''

        :param train_epochs: epochs to train
        :param start_date: start date for parse data
        :param end_date: end date for parse data
        :param batch_size: batch_size for dataloader
        :param history_window_size: window size for historical analysis
        :param val_ratio: ratio between train and validation data in dataloader
        '''
        processed_data = self.prepare_data_to_train(self.symbol, start_date, end_date, history_window_size)
        train_loader, test_loader = processed_data.get_loaders_train(val_ratio, batch_size)
        optim = torch.optim.Adam(self.model.parameters(), lr=0.001, weight_decay=1e-3)
        loss_fn = torch.nn.MSELoss()
        running_loss = 0.0
        for epoch in range(train_epochs):
            self.model.train()
            for batch_index, data in enumerate(train_loader):
                x, y = data
                x = x.to(self.device)
                y = y.to(self.device)
                output = self.model(x)
                loss = loss_fn(output, y[:, 0, :])
                running_loss += loss.item()
                optim.zero_grad()
                loss.backward()
                optim.step()
                if batch_index % (len(train_loader) // 3) == 1:  # print every 100 batches
                    avg_loss_across_batches = running_loss / (len(train_loader) // 3)
                    print(f'[epoch]{epoch} Loss: {avg_loss_across_batches}')
                    running_loss = 0.0
            self.model.eval()
            val_running_loss = 0
            with torch.no_grad():
                for batch_index, data in enumerate(test_loader):
                    x, y = data
                    x = x.to(self.device)
                    y = y.to(self.device)
                    output = self.model(x)
                    loss = loss_fn(output, y[:, 0, :])
                    val_running_loss += loss.item()
                print(f"validation loss: {val_running_loss / len(test_loader)}")
