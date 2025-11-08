from omegaconf import DictConfig
import hydra
import torch
import numpy as np
import sys
from pathlib import Path

# Hack to get access to root directory
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))
from training.networks import SimpleEEGNet  # MUST BE SAME NETWORK USED IN TRAINING

@hydra.main(config_path="../../configs", config_name="main_config", version_base=None)
def main(cfg: DictConfig):
    """Attempt to inference a users mental state from the model used in train.py"""
    model = SimpleEEGNet(
        n_channels=cfg.model.n_channels,
        n_classes=cfg.model.n_classes,
    )

    state_dict = torch.load(cfg.inference.model_filepath, map_location=cfg.system.accelerator)
    new_state_dict = {k.replace("model.", ""): v for k, v in state_dict.items()}
    model.load_state_dict(new_state_dict)

    model.eval()

    # TODO Example input: 1s of EEG at 256Hz, 4 channels
    x = simulate_eeg_data(duration=10)  # Simulate 10 seconds of EEG data
    x = torch.from_numpy(x).float().view(1, 4, -1)  # Ensure x is a float tensor with shape (1, 4, sequence_length)
    labels = list(cfg.model.labels.keys())

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


def simulate_eeg_data(duration=60, sampling_rate=1, channels=4):
    """
    Simulate EEG data for TP9, AF7, AF8, and TP10 channels.

    Args:
        duration (int, optional): Duration of the simulation in seconds. Defaults to 60.
        sampling_rate (int, optional): Sampling rate in Hz. Defaults to 1.
        channels (int, optional): Number of channels. Defaults to 4.

    Returns:
        np.ndarray: Simulated EEG data with shape (samples, channels).
    """
    samples = int(duration * sampling_rate)
    data = np.random.normal(0, 1, size=(samples, channels))
    return data



if __name__ == "__main__":
    main()
