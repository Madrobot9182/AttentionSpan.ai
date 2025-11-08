import pytorch_lightning as pl
import torch
from torch import nn
import torch.nn.functional as F
from torchmetrics import Accuracy
from torchmetrics.regression import MeanAbsoluteError, R2Score
from networks import MultiTaskEEGModel


class LitMultiTaskEEG(pl.LightningModule):
    def __init__(self, cfg):
        super().__init__()
        self.save_hyperparameters()
        self.model = MultiTaskEEGModel(
            n_channels=cfg.model.n_channels,
            hidden_dims=cfg.model.hidden_dims,
            n_classes=cfg.model.n_classes,
            n_outputs=cfg.model.n_outputs,
        )

        # Define losses
        self.ce_loss = nn.CrossEntropyLoss()
        self.mse_loss = nn.MSELoss()

        # Metrics
        self.acc = Accuracy(task="multiclass", num_classes=cfg.model.n_classes)
        self.mae = MeanAbsoluteError()

        self.lr = cfg.train.lr

    def forward(self, x):
        return self.model(x)

    def training_step(self, batch, batch_idx):
        x, (y_class, y_reg) = batch
        logits, reg_out = self(x)
        loss_class = self.ce_loss(logits, y_class)
        loss_reg = self.mse_loss(reg_out, y_reg)
        loss = loss_class + 0.5 * loss_reg  # Weighted sum — tune as needed
        self.log_dict({"train_loss": loss, "train_acc": self.acc(logits, y_class), "train_mae": self.mae(reg_out, y_reg)})
        return loss

    def validation_step(self, batch, batch_idx):
        x, (y_class, y_reg) = batch
        logits, reg_out = self(x)
        loss_class = self.ce_loss(logits, y_class)
        loss_reg = self.mse_loss(reg_out, y_reg)
        loss = loss_class + 0.5 * loss_reg
        self.log_dict({"val_loss": loss, "val_acc": self.acc(logits, y_class), "val_mae": self.mae(reg_out, y_reg)}, prog_bar=True)
        return loss

    def configure_optimizers(self):
        return torch.optim.AdamW(self.parameters(), lr=self.lr)