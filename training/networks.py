import torch
import torch.nn as nn

class SimpleEEGNet(nn.Module):
    def __init__(self, n_channels=4, n_classes=3, hidden_dims=(16, 32)):
        super().__init__()
        self.conv1 = nn.Conv1d(n_channels, hidden_dims[0], kernel_size=5, padding=2)
        self.bn1 = nn.BatchNorm1d(hidden_dims[0])
        self.conv2 = nn.Conv1d(hidden_dims[0], hidden_dims[1], kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm1d(hidden_dims[1])
        self.pool = nn.AdaptiveAvgPool1d(1)
        self.fc = nn.Linear(hidden_dims[1], n_classes)
        self.relu = nn.ReLU()


    def forward(self, x):
        # Expected x: (batch, channels, samples)
        x = self.relu(self.bn1(self.conv1(x)))
        x = self.relu(self.bn2(self.conv2(x)))
        x = self.pool(x).squeeze(-1)
        return self.fc(x)
