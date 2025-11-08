from omegaconf import DictConfig
import hydra

from models import LitClassifier
from networks import SimpleEEGNet
from musedataloader import MuseEEGDataset

import pytorch_lightning as pl
import torch
from torch.utils.data import Dataset, random_split

from pathlib import Path
import datetime


@hydra.main(config_path="../configs", config_name="training", version_base=None)
def main(cfg: DictConfig):
    """Train the Muse 2 Classifier from the data"""
    print(
        f"Using lr={cfg.train.lr}, batch_size={cfg.train.batch_size}, epochs={cfg.train.epochs}"
    )

    # Define the model (torch network)
    base_model = SimpleEEGNet(
        n_channels=cfg.model.n_channels,
        n_classes=cfg.model.n_classes,
    )

    # Wrap in the LightningModule
    lit_model = LitClassifier(base_model, cfg)

    # Create the Lightning trainer
    trainer = pl.Trainer(
        max_epochs=cfg.train.epochs,
        accelerator=cfg.system.accelerator,
        devices=cfg.system.devices,
    )

    # Get the datamodule/DataLoader, split into train and test sets
    dataset = MuseEEGDataset("data", window_size=512, step_size=256)
    n_total = len(dataset)
    n_train = int(0.8 * n_total)
    n_val = n_total - n_train

    train_dataset, val_dataset = random_split(dataset, [n_train, n_val])

    trainer.fit(lit_model, train_dataloaders=train_dataset, val_dataloaders=val_dataset)

    # Save to model directory
    save_model_checkpoint(trainer, lit_model, cfg.system.model_output_filepath)


def save_model_checkpoint(
    trainer: pl.Trainer, model: pl.LightningModule, output_dir: str
):
    """Save both checkpoint and model weights to disk."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    output_time = datetime.datetime.now().strftime("%Y-%m-%d")

    # Save full checkpoint (for resuming training)
    ckpt_path = Path(output_dir, "checkpoints")
    Path(ckpt_path).mkdir(parents=True, exist_ok=True)

    trainer.save_checkpoint(Path(ckpt_path, f"{output_time}-model_checkpoint.ckpt"))
    print(f"[green]Saved checkpoint to {ckpt_path}")

    # Save model weights only (for inference)
    model_path = Path(output_dir, "models")
    Path(model_path).mkdir(parents=True, exist_ok=True)

    torch.save(model.state_dict(), Path(model_path, f"{output_time}-model.pt"))
    print(f"[green]Saved model weights to {model_path}")


if __name__ == "__main__":
    main()
