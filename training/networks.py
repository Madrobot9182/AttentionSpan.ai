import torch
import torch.nn as nn
import torch.nn.functional as F


class MultiTaskEEGModel(nn.Module):
    def __init__(self, n_channels=4, hidden_dims=(16, 32), n_classes=3, n_outputs=3):
        super().__init__()
        # Shared feature extractor
        self.conv1 = nn.Conv1d(n_channels, hidden_dims[0], kernel_size=5, padding=2)
        self.bn1 = nn.BatchNorm1d(hidden_dims[0])
        self.conv2 = nn.Conv1d(hidden_dims[0], hidden_dims[1], kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm1d(hidden_dims[1])
        self.pool = nn.AdaptiveAvgPool1d(1)
        self.relu = nn.ReLU()

        # Task-specific heads
        self.fc_class = nn.Linear(hidden_dims[1], n_classes)
        self.fc_reg = nn.Linear(hidden_dims[1], n_outputs)

    def forward(self, x):
        # Shared encoding
        x = self.relu(self.bn1(self.conv1(x)))
        x = self.relu(self.bn2(self.conv2(x)))
        x = self.pool(x).squeeze(-1)  # (B, hidden_dims[1])

        # Two heads
        class_logits = self.fc_class(x)
        reg_outputs = self.fc_reg(x)

        return class_logits, reg_outputs
