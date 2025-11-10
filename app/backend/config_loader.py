from hydra import initialize, compose
from omegaconf import OmegaConf
from pathlib import Path
import os

def load_config(config_name="main_config.yaml"):
    # Detect true project root
    project_root = Path(__file__).resolve().parents[2]  # ✅ this points to project root
    config_dir = project_root / "configs"

    rel_config_dir = os.path.relpath(config_dir, Path.cwd())

    with initialize(config_path=rel_config_dir, version_base=None):
        cfg = compose(config_name=Path(config_name).stem)

    # Normalize important paths to absolute
    if "inference" in cfg and "model_filepath" in cfg.inference:
        model_path = Path(cfg.inference.model_filepath)
        if not model_path.is_absolute():
            cfg.inference.model_filepath = str((project_root / model_path).resolve())

    if "training" in cfg and "data_dir" in cfg.training:
        data_path = Path(cfg.training.data_dir)
        if not data_path.is_absolute():
            cfg.training.data_dir = str((project_root / data_path).resolve())

    return cfg
