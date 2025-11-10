import torch
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import numpy as np
from pathlib import Path
from omegaconf import DictConfig


class MuseEEGDataset(Dataset):
    def __init__(
        self, data_dir, labels, channel_labels, regression_targets, window_size=512, step_size=256, transform=None,
    ):
        self.data_dir = data_dir
        self.labels = labels
        self.window_size = window_size
        self.step_size = step_size
        self.transform = transform
        self.samples = []
        self.regression_targets = regression_targets
        self.channel_labels = channel_labels
        self.sessions = {}

        # Get parquet files of each session
        for file_path in Path(self.data_dir).glob("*.parquet"):
            df = pd.read_parquet(file_path)
            
            data = df[self.channel_labels].to_numpy(dtype=np.float32)
            reg_data = df[self.regression_targets].to_numpy(dtype=np.float32)
            class_labels = df["Label_Class"].to_numpy(dtype=np.int64)
            self.sessions[file_path] = data
            print(f"Loaded {len(df)} rows from {file_path}")

            # Create overlapping windows
            for start in range(0, len(data) - window_size, step_size):
                end = start + window_size

                # Use the mean target values over the window
                reg_target = np.mean(reg_data[start:end], axis=0).astype(np.float32)
                class_target = int(class_labels[end - 1])  # last label in window
                print(f"Data shape: {data.shape}, reg shape: {reg_target.shape}")

                self.samples.append((file_path, start, end, reg_target, class_target))



    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        session_path, start, end, reg_target, class_target = self.samples[idx]
        data = self.sessions[session_path]
        x = data[start:end]
        x = torch.from_numpy(x).float().T  # (4, 512)

        # Classification label
        # y_class = torch.tensor(label_id, dtype=torch.long)
        y_class = torch.tensor(class_target, dtype=torch.long)
        
        # Regression target TODO (replace this with your actual continuous label data)
        # e.g. normalized focus/unfocus/fatigue levels in [0, 1]
        # y_reg = torch.rand(11, dtype=torch.float32)
        y_reg = torch.tensor(reg_target, dtype=torch.float32)  # shape (3,)
        
        return x, (y_class, y_reg)



# Used in DataLoader to correctly stack the data
def collate_fn(batch):
    xs = torch.stack([item[0] for item in batch])  # (B, 4, 512)

    # separate class and regression labels
    y_class = torch.stack([item[1][0] for item in batch])  # (B,)
    y_reg   = torch.stack([item[1][1] for item in batch])  # (B, n_outputs)

    return xs, (y_class, y_reg)



def create_dataloaders(train_dataset, val_dataset, test_dataset, cfg: DictConfig):
    common_args = dict(
        batch_size=cfg.train.batch_size,
        num_workers=cfg.train.num_workers,       
        pin_memory=(cfg.system.accelerator != "cpu"),     # Speeds up host→GPU transfer
        persistent_workers=True,  # Keeps workers alive between epochs
        collate_fn=collate_fn,
    )

    train_loader = DataLoader(train_dataset, shuffle=True, **common_args)
    val_loader = DataLoader(val_dataset, shuffle=False, **common_args)
    test_loader = DataLoader(test_dataset, shuffle=False, **common_args) if test_dataset else None

    return train_loader, val_loader, test_loader
