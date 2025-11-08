import torch
from torch.utils.data import Dataset
import pandas as pd
import numpy as np
from pathlib import Path

class MuseEEGDataset(Dataset):
    def __init__(self, root_dir, window_size=512, step_size=256, transform=None):
        self.root_dir = Path(root_dir)
        self.window_size = window_size
        self.step_size = step_size
        self.transform = transform
        self.samples = []
        self.sessions = {}

        for session_path in sorted(self.root_dir.glob("session_*/eeg.parquet")):
            df = pd.read_parquet(session_path)
            data = df[["TP9","AF7","AF8","TP10"]].to_numpy(dtype=np.float32)
            self.sessions[session_path] = data

            for start in range(0, len(data) - window_size, step_size):
                end = start + window_size
                self.samples.append((session_path, start, end))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        session_path, start, end = self.samples[idx]
        data = self.sessions[session_path]
        x = data[start:end]
        if self.transform:
            x = self.transform(x)
        return torch.from_numpy(x)