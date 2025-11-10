# backend/inference_thread.py
import threading
import time
from muse_streaming import MuseRealtimeInference
import torch
from config_loader import load_config

# reference to global dict from Flask
def run_inference_background(shared_dict):
    try:
        base_dir = Path(hydra.utils.get_original_cwd())
    except Exception:
        # If Hydra isn't running (e.g., normal Flask app), fallback to script parent
        base_dir = Path(__file__).resolve().parents[1]
    return base_dir / filename

    cfg = load_config()

    
    model = MultiTaskEEGModel(
        n_channels=cfg.model.n_channels,
        hidden_dims=cfg.model.hidden_dims,
        n_classes=cfg.model.n_classes,
        n_outputs=cfg.model.n_outputs,
    )
    model.load_state_dict(torch.load(cfg.inference.model_filepath, map_location="cpu"))
    model.eval()

    muse = MuseRealtimeInference("COM7", model, cfg)
    muse.connect_muse()

    while True:
        eeg_data, band_powers, gyro_mean, accel_mean = muse.get_burst_data(1.0)
        _, class_label, _, _ = muse.predict_state(eeg_data, band_powers, gyro_mean, accel_mean)

        shared_dict["class_label"] = class_label
        shared_dict["timestamp"] = time.time()
        time.sleep(1)  # 1-second updates