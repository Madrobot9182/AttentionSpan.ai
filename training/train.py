# train.py
import pytorch_lightning as pl
from omegaconf import DictConfig
import hydra

from models import LitClassifier
from networks import SimpleEEGNet

@hydra.main(config_path="../configs", config_name="training", version_base=None)
def main(cfg: DictConfig):
    print(f"Using lr={cfg.train.lr}, batch_size={cfg.train.batch_size}, epochs={cfg.train.epochs}")

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

    # TODO Get the datamodule/DataLoader
    # train_loader = ...
    # val_loader = ...

    trainer.fit(lit_model, train_dataloaders=train_loader, val_dataloaders=val_loader)

if __name__ == "__main__":
    main()
