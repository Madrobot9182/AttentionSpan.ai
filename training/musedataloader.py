import torch
from torch.utils.data import Dataset
import pandas as pd
import numpy as np
from pathlib import Path


class MuseEEGDataset(Dataset):
    def __init__(
        self, data_dir, labels, window_size=512, step_size=256, transform=None
    ):
        self.data_dir = data_dir
        self.labels = labels
        self.window_size = window_size
        self.step_size = step_size
        self.transform = transform
        self.samples = []
        self.sessions = {}

        # Get parquet files of each session
        for session_dir in sorted(Path(self.data_dir).glob("session_*")):
            for file_path in session_dir.glob("*.parquet"):
                label_name = file_path.stem.split("_")[-1]
                if label_name not in labels:
                    continue  # Unknown files
                label = labels[label_name]
                df = pd.read_parquet(file_path)

                # TODO change later
                data = df[["TP9", "AF7", "AF8", "TP10"]].to_numpy(dtype=np.float32)
                self.sessions[file_path] = data  # Cache result

                # Segment into overlapping windows
                for start in range(0, len(data) - window_size, step_size):
                    end = start + window_size
                    self.samples.append((file_path, start, end, label))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        session_path, start, end, label = self.samples[idx]
        data = self.sessions[session_path]
        x = data[start:end]
        if self.transform:
            x = self.transform(x)
        x = torch.from_numpy(x).float().T
        y = torch.tensor(label, dtype=torch.long)
        return x, y


# Used in DataLoader to correctly stack the data
def collate_fn(batch):
    xs = torch.stack([item[0] for item in batch])  # shape (B, 4, 512)
    ys = torch.tensor([item[1] for item in batch], dtype=torch.long)
    return xs, ys
