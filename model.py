import torch, torch.nn as nn


class LSTM(nn.Module):
    def __init__(self, input_size, hidden_size, num_stacked_layers, device):
        super().__init__()
        self.device = device
        self.hidden_size = hidden_size
        self.num_stacked_layers = num_stacked_layers

        self.lstm1 = nn.LSTM(input_size, hidden_size, num_stacked_layers,
                             batch_first=True, dropout=0.2)
        self.lstm2 = nn.LSTM(hidden_size, hidden_size, num_stacked_layers,
                             batch_first=True, dropout=0.2)
        self.lstm3 = nn.LSTM(hidden_size, hidden_size, num_stacked_layers,
                             batch_first=True, dropout=0.2)
        self.lstm4 = nn.LSTM(hidden_size, hidden_size, num_stacked_layers,
                             batch_first=True, dropout=0.2)
        self.fc = nn.Linear(hidden_size, 16)
        self.fc1 = nn.Linear(16, 1)
        self.relu = torch.nn.ReLU()

    def forward(self, x):
        batch_size = x.size(0)

        h0 = torch.zeros(self.num_stacked_layers, batch_size, self.hidden_size).to(self.device)
        c0 = torch.zeros(self.num_stacked_layers, batch_size, self.hidden_size).to(self.device)

        x, (h_out, c_out) = self.lstm1(x, (h0, c0))
        x, (h_out, c_out) = self.lstm2(x, (h_out, c_out))
        x, (h_out, c_out) = self.lstm3(x, (h_out, c_out))
        x, (h_out, c_out) = self.lstm4(x, (h_out, c_out))
        h_out = h_out.view(-1, self.hidden_size)
        out = self.relu(self.fc(h_out))
        out = self.fc1(out)
        return out
