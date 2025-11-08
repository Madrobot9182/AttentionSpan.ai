import pytorch_lightning as pl
import torch
import torch.nn.functional as F
from torchmetrics import Accuracy

class LitClassifier(pl.LightningModule):
    def __init__(self, model: torch.nn.Module, cfg):
        super().__init__()
        self.model = model
        self.lr = cfg.train.lr
        self.acc = Accuracy(task="multiclass", num_classes=10)

    def forward(self, x):
        return self.model(x)

    def training_step(self, batch, batch_idx):
        x, y = batch
        y_hat = self(x)
        loss = F.cross_entropy(y_hat, y)
        self.acc.update(y_hat, y)
        self.log("train_loss", loss, prog_bar=True)
        self.log("train_acc", self.acc, prog_bar=True)
        return loss

    def configure_optimizers(self):
        return torch.optim.AdamW(self.parameters(), lr=self.lr)
