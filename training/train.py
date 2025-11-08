from omegaconf import DictConfig
import hydra
from hydra.utils import get_original_cwd

from models import LitMultiTaskEEG
# from networks import MultiTaskEEGModel
from musedataloader import MuseEEGDataset, create_dataloaders

import pytorch_lightning as pl
import torch
from torch.utils.data import Dataset, DataLoader, random_split

from pathlib import Path
import datetime


@hydra.main(config_path="../configs", config_name="training", version_base=None)
def main(cfg: DictConfig):
    """Train the Muse 2 Classifier from the data"""
    # Create in the LightningModule
    lit_model = LitMultiTaskEEG(cfg)

    # Create the Lightning trainer
    trainer = pl.Trainer(
        max_epochs=cfg.train.epochs,
        accelerator=cfg.system.accelerator,
        devices=cfg.system.devices,
        logger=False,
        enable_checkpointing=False,
    )

    # Get the datamodule/DataLoader, split into train and test sets
    data_dir = Path(get_original_cwd(), cfg.system.data_filepath)
    dataset = MuseEEGDataset(data_dir, cfg.model.labels, window_size=512, step_size=256)

    train_dataset, val_dataset = random_split(dataset, [0.8, 0.2])
    train_loader, val_loader, _ = create_dataloaders(
        train_dataset, val_dataset, test_dataset=None, cfg=cfg
    )
    # Train the model (fitting the weights)
    trainer.fit(lit_model, train_dataloaders=train_loader, val_dataloaders=val_loader)

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
    print(f"\033[92mSaved checkpoint to {ckpt_path}")

    # Save model weights only (for inference)
    model_path = Path(output_dir, "models")
    Path(model_path).mkdir(parents=True, exist_ok=True)

    torch.save(model.state_dict(), Path(model_path, f"{output_time}-model.pt"))
    print(f"\033[92mSaved model weights to {model_path}")


if __name__ == "__main__":
    main()
