from omegaconf import DictConfig
import hydra
from networks import SimpleEEGNet  # MUST BE SAME NETWORK USED IN TRAINING
import torch


@hydra.main(config_path="../configs", config_name="training", version_base=None)
def main(cfg: DictConfig):
    """Attempt to inference a users mental state from the model used in train.py"""
    model = SimpleEEGNet(
        n_channels=cfg.model.n_channels,
        n_classes=cfg.model.n_classes,
    )
    model.load_state_dict(
        torch.load(cfg.inference.weights_filepath, map_location=cfg.system.accelerator)
    )
    model.eval()

    # TODO Example input: 1s of EEG at 256Hz, 4 channels
    x = torch.randn(1, 256, 4).view(1, -1)
    labels = ["focused", "distracted", "fatigued"]

    probs, state = predict_state(model, x, labels)
    print(probs)
    print("Predicted:", state)


def predict_state(model, x, labels):
    model.eval()
    with torch.no_grad():
        logits = model(x)
        probs = torch.softmax(logits, dim=1)
        pred_class = torch.argmax(probs, dim=1)
    return {label: float(p) for label, p in zip(labels, probs[0])}, labels[
        pred_class.item()
    ]


if __name__ == "__main__":
    main()
