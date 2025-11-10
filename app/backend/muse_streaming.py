from brainflow.board_shim import (
    BoardShim,
    BrainFlowInputParams,
    BoardIds,
    BrainFlowPresets,
)
from brainflow.data_filter import (
    DataFilter,
    FilterTypes,
    WindowOperations,
    DetrendOperations,
)
import numpy as np
import time
import datetime
import torch
from pathlib import Path
from omegaconf import DictConfig
import hydra
import sys
from config_loader import load_config

# Hack to get access to root directory
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))
from training.networks import MultiTaskEEGModel


class MuseRealtimeInference:
    board: BoardShim
    boardId = 38
    con_port: str

    def __init__(self, con_port, model, cfg):
        self.con_port = con_port
        self.model = model
        self.cfg = cfg
    def connect_muse(self):
        try:
            params = BrainFlowInputParams()
            params.serial_port = self.con_port
            self.board = BoardShim(self.boardId, params)
            self.board.prepare_session()
            return True
        except Exception as e:
            return False

    def process_eeg_burst(self, burst_duration: float = 1.0):
        """
        Collects and preprocesses a short EEG burst from the Muse 2 headset.

        Includes:
        - Bandpass (1–50 Hz) and notch (50/60 Hz) filtering
        - Amplitude & motion artifact rejection
        - Bandpower extraction (Delta–Gamma)

        Returns:
            dict:
                {
                    "eeg_data": np.ndarray (n_channels, n_samples),
                    "band_powers": dict,
                    "gyro_mean": np.ndarray(3,),
                    "accel_mean": np.ndarray(3,)
                }
            or None if invalid / noisy burst.
        """
        # Wait for buffer to fill with new data
        time.sleep(burst_duration)

        # --- 🔹 1. Grab new board data ---
        try:
            data = self.board.get_board_data()
        except Exception as e:
            print(f"❌ Failed to read Muse data: {e}")
            return None

        eeg_channels = self.board.get_eeg_channels(self.boardId)
        eeg_data = data[eeg_channels]

        try:
            aux_data = self.board.get_board_data(
                preset=BrainFlowPresets.AUXILIARY_PRESET
            )
        except Exception:
            aux_data = np.zeros((6, eeg_data.shape[1]))

        # --- 🔹 2. Validate Data Shapes ---
        if eeg_data.shape[1] < 32:
            print(f"⚠️ Not enough EEG samples ({eeg_data.shape[1]}). Skipping burst.")
            return None

        # --- 🔹 3. Extract Gyro / Accel Means ---
        if aux_data.shape[0] >= 6:
            accel_data = aux_data[0:3, :]
            gyro_data = aux_data[3:6, :]
            gyro_mean = np.mean(gyro_data, axis=1)
            accel_mean = np.mean(accel_data, axis=1)
        else:
            gyro_mean = np.zeros(3)
            accel_mean = np.zeros(3)

        # --- 🔹 4. Filtering ---
        eeg_data = np.ascontiguousarray(eeg_data)
        sampling_rate = self.board.get_sampling_rate(self.boardId)

        for ch in range(eeg_data.shape[0]):
            try:
                DataFilter.detrend(eeg_data[ch], DetrendOperations.CONSTANT.value)
                DataFilter.perform_bandpass(
                    eeg_data[ch],
                    sampling_rate,
                    1.0,
                    50.0,
                    2,
                    FilterTypes.BUTTERWORTH.value,
                    0,
                )
                # North America (60 Hz)
                DataFilter.perform_bandstop(
                    eeg_data[ch],
                    sampling_rate,
                    58.0,
                    62.0,
                    2,
                    FilterTypes.BUTTERWORTH.value,
                    0,
                )
                # Europe (50 Hz)
                DataFilter.perform_bandstop(
                    eeg_data[ch],
                    sampling_rate,
                    48.0,
                    52.0,
                    2,
                    FilterTypes.BUTTERWORTH.value,
                    0,
                )
            except Exception as e:
                print(f"Filter error on channel {ch}: {e}")
                return None

        # --- 🔹 5. Artifact Rejection ---
        # remove amplitude spikes (>100 µV)
        amplitude_mask = np.all(np.abs(eeg_data) < 250.0, axis=0)
        eeg_data = eeg_data[:, amplitude_mask]

        if eeg_data.shape[1] < 32:
            print("⚠️ Burst rejected due to amplitude artifacts.")
            return None

        # Motion artifacts from accelerometer
        accel_magnitude = np.linalg.norm(accel_data, axis=0)
        delta_accel = np.diff(accel_magnitude)
        motion_score = np.mean(np.abs(delta_accel))
        if motion_score > 0.5:  # Adjust if too sensitive
            print("⚠️  High motion detected — skipping burst.")
            return None

        # --- 🔹 6. Ensure Even-Length Array for Bandpower ---
        if eeg_data.shape[1] % 2 == 1:
            eeg_data = eeg_data[:, :-1]
        eeg_data = np.ascontiguousarray(eeg_data)

        # --- 🔹 7. Bandpower Extraction ---
        try:
            avgs, stds = DataFilter.get_avg_band_powers(
                eeg_data,
                channels=np.arange(eeg_data.shape[0]),
                sampling_rate=sampling_rate,
                apply_filter=False,
            )
            band_powers = {
                "Delta": float(avgs[0]),
                "Theta": float(avgs[1]),
                "Alpha": float(avgs[2]),
                "Beta": float(avgs[3]),
                "Gamma": float(avgs[4]),
            }
        except Exception as e:
            print(f"❌ Bandpower calculation failed: {e}")
            return None

        # --- ✅ Return structured burst data ---
        return {
            "eeg_data": eeg_data,
            "band_powers": band_powers,
            "gyro_mean": gyro_mean,
            "accel_mean": accel_mean,
        }

    def get_clean_burst_data(self, duration_seconds=1.0):
        """
        Shorter version of get_avg_wave_data() for real-time inference.
        Performs filtering, motion rejection, and bandpower extraction.
        """
        time.sleep(duration_seconds)
        data = self.board.get_board_data()
        eeg_data = data[self.board.get_eeg_channels(self.boardId)]
        aux_data = self.board.get_board_data(preset=BrainFlowPresets.AUXILIARY_PRESET)

        if eeg_data.shape[1] < 16:
            print("⚠️ Not enough EEG samples.")
            return None

        if aux_data.shape[0] >= 6:
            accel_data = aux_data[0:3, :]
            gyro_data = aux_data[3:6, :]
            gyro_mean = np.mean(gyro_data, axis=1)
            accel_mean = np.mean(accel_data, axis=1)
        else:
            gyro_mean = [0, 0, 0]
            accel_mean = [0, 0, 0]

        sampling_rate = self.board.get_sampling_rate(self.boardId)
        eeg_data = np.ascontiguousarray(eeg_data)

        # Basic cleaning (bandpass + bandstop + detrend)
        for ch in range(eeg_data.shape[0]):
            DataFilter.detrend(eeg_data[ch], DetrendOperations.CONSTANT.value)
            DataFilter.perform_bandpass(
                eeg_data[ch],
                sampling_rate,
                1.0,
                50.0,
                2,
                FilterTypes.BUTTERWORTH.value,
                0,
            )
            DataFilter.perform_bandstop(
                eeg_data[ch],
                sampling_rate,
                58.0,
                62.0,
                2,
                FilterTypes.BUTTERWORTH.value,
                0,
            )
            DataFilter.perform_bandstop(
                eeg_data[ch],
                sampling_rate,
                48.0,
                52.0,
                2,
                FilterTypes.BUTTERWORTH.value,
                0,
            )

        # Artifact rejection
        amplitude_mask = np.all(np.abs(eeg_data) < 100.0, axis=0)
        eeg_data = eeg_data[:, amplitude_mask]
        std_mask = np.std(eeg_data, axis=0) < np.percentile(
            np.std(eeg_data, axis=0), 95
        )
        eeg_data = eeg_data[:, std_mask]

        # Motion check
        accel_magnitude = np.linalg.norm(accel_data, axis=0)
        delta_accel = np.diff(accel_magnitude)
        if np.mean(np.abs(delta_accel)) > 0.5:
            print("⚠️ Motion too high, skipping burst.")
            return None

        # Band powers
        eeg_data = np.ascontiguousarray(
            eeg_data[:, : int(sampling_rate * duration_seconds)]
        )
        avgs, _ = DataFilter.get_avg_band_powers(
            eeg_data,
            channels=np.arange(eeg_data.shape[0]),
            sampling_rate=sampling_rate,
            apply_filter=False,
        )

        band_powers = {
            "Delta": avgs[0],
            "Theta": avgs[1],
            "Alpha": avgs[2],
            "Beta": avgs[3],
            "Gamma": avgs[4],
        }

        return eeg_data, band_powers, gyro_mean, accel_mean

    def predict_state(self, eeg_data, band_powers, gyro_mean, accel_mean):
        """
        Run inference on EEG data

        Args:
            eeg_data: numpy array of shape (n_channels, n_samples)
            band_powers: dict with Delta, Theta, Alpha, Beta, Gamma
            gyro_mean: list [x, y, z]
            accel_mean: list [x, y, z]

        Returns:
            class_probs: dict of probabilities for each class
            class_label: predicted class label
            reg_output: regression outputs
            feature_dict: dict with all features for logging
        """
        # labels = list(self.cfg.model.labels.keys())
        labels = [
            "Focus-NotFatigued",
            "Focus-Fatigued",
            "UnFocus-NotFatigued",
            "UnFocus-Fatigued",
        ]

        # Model expects 11 channels: [Delta, Theta, Alpha, Beta, Gamma, GyroX, GyroY, GyroZ, AccelX, AccelY, AccelZ]
        # Create feature array by repeating the scalar values across time samples
        n_samples = eeg_data.shape[1]

        # Stack all 11 features
        features = np.array(
            [
                np.full(n_samples, band_powers["Delta"]),
                np.full(n_samples, band_powers["Theta"]),
                np.full(n_samples, band_powers["Alpha"]),
                np.full(n_samples, band_powers["Beta"]),
                np.full(n_samples, band_powers["Gamma"]),
                np.full(n_samples, gyro_mean[0]),
                np.full(n_samples, gyro_mean[1]),
                np.full(n_samples, gyro_mean[2]),
                np.full(n_samples, accel_mean[0]),
                np.full(n_samples, accel_mean[1]),
                np.full(n_samples, accel_mean[2]),
            ]
        )  # Shape: (11, n_samples)

        # Convert to tensor and add batch dimension
        # Expected shape: (batch=1, 11 channels, n_samples)
        x = torch.from_numpy(features).float().unsqueeze(0)

        with torch.no_grad():
            class_out, reg_out = self.model(x)
            probs = torch.softmax(class_out, dim=1)
            pred_class = torch.argmax(probs, dim=1)

        class_probs = {label: float(p) for label, p in zip(labels, probs[0])}
        class_label = labels[pred_class.item()]
        reg_output = reg_out[0].cpu().numpy()

        # Create feature dict in the same format as training data
        # FO-NF, FO-FA, UF-NF, UF-FA are placeholders (regression targets you'll fill later)
        feature_dict = {
            "Delta": band_powers["Delta"],
            "Theta": band_powers["Theta"],
            "Alpha": band_powers["Alpha"],
            "Beta": band_powers["Beta"],
            "Gamma": band_powers["Gamma"],
            "GyroX": gyro_mean[0],
            "GyroY": gyro_mean[1],
            "GyroZ": gyro_mean[2],
            "AccelX": accel_mean[0],
            "AccelY": accel_mean[1],
            "AccelZ": accel_mean[2],
            "FO-NF": 0.0,  # Placeholder - fill with actual value later
            "FO-FA": 0.0,  # Placeholder - fill with actual value later
            "UF-NF": 0.0,  # Placeholder - fill with actual value later
            "UF-FA": 0.0,  # Placeholder - fill with actual value later
            "Label_Class": class_label,
        }

        return class_probs, class_label, reg_output, feature_dict

    def run_realtime_inference(
        self, burst_duration=1.0, max_iterations=None, save_csv=None
    ):
        if not self.board:
            print("Board not connected!")
            return

        print(f"Starting streaming with {burst_duration}s bursts...")
        self.board.start_stream()
        time.sleep(5)

        if save_csv:
            headers = "Delta,Theta,Alpha,Beta,Gamma,GyroX,GyroY,GyroZ,AccelX,AccelY,AccelZ,FO-NF,FO-FA,UF-NF,UF-FA,Label_Class"
            with open(save_csv, "w") as f:
                f.write(headers + "\n")

        iteration = 0
        try:
            while max_iterations is None or iteration < max_iterations:
                burst = self.process_eeg_burst()
                if burst is None:
                    continue  # skip bad burst

                bp = burst["band_powers"]
                feature_dict = burst["feature_dict"]

                # inference
                class_probs, class_label, reg_output, feature_dict = self.predict_state(
                    None, bp, burst["gyro_mean"], burst["accel_mean"]
                )

                result = {
                    "timestamp": time.time(),
                    "iteration": iteration,
                    "class_probs": class_probs,
                    "class_label": class_label,
                    "reg_output": reg_output.tolist(),
                    "features": feature_dict,
                }
                self.results_history.append(result)

                if save_csv:
                    with open(save_csv, "a") as f:
                        csv_line = ",".join(
                            str(feature_dict[k])
                            for k in [
                                "Delta",
                                "Theta",
                                "Alpha",
                                "Beta",
                                "Gamma",
                                "GyroX",
                                "GyroY",
                                "GyroZ",
                                "AccelX",
                                "AccelY",
                                "AccelZ",
                                "FO-NF",
                                "FO-FA",
                                "UF-NF",
                                "UF-FA",
                                "Label_Class",
                            ]
                        )
                        f.write(csv_line + "\n")

                print(f"\n--- Iteration {iteration} ---")
                print(f"Predicted State: {class_label}")
                print(f"Probabilities: {class_probs}")
                print(f"Regression Output: {reg_output}")

                iteration += 1

        except KeyboardInterrupt:
            print("\nStopping inference...")
        finally:
            self.board.stop_stream()

    def run_realtime_inference_generator(self, burst_duration: float = 1.0):
        """
        Continuously yields inference results after fully processing EEG bursts
        (bandpass, artifact rejection, bandpower extraction, etc.).

        Returns the same format as before:
            {
                "timestamp": float,
                "iteration": int,
                "class_probs": dict,
                "class_label": str,
                "reg_output": list,
                "features": dict
            }
        """
        if not self.board:
            print("⚠️ Board not connected!")
            return

        print(f"🎧 Starting Muse streaming ({burst_duration}s bursts)...")
        self.board.start_stream()
        time.sleep(burst_duration * 2)

        iteration = 0
        try:
            while True:
                # 🧠 Step 1 — Process a single burst of EEG data safely
                burst = self.process_eeg_burst(burst_duration=burst_duration)

                # If cleaning step rejected data (e.g. too noisy / motion artifact), skip
                if burst is None or burst.get("eeg_data") is None:
                    print(
                        "⚠️ Skipping invalid EEG burst (empty or motion-contaminated)."
                    )
                    continue

                eeg_data = burst["eeg_data"]
                band_powers = burst["band_powers"]
                gyro_mean = burst["gyro_mean"]
                accel_mean = burst["accel_mean"]

                # 🧩 Step 2 — Run the model prediction
                try:
                    class_probs, class_label, reg_output, feature_dict = (
                        self.predict_state(eeg_data, band_powers, gyro_mean, accel_mean)
                    )
                except Exception as e:
                    print(f"❌ Model inference failed: {e}")
                    continue

                # 🧾 Step 3 — Yield the structured result
                yield {
                    "timestamp": time.time(),
                    "iteration": iteration,
                    "class_probs": class_probs,
                    "class_label": class_label,
                    "reg_output": (
                        reg_output.tolist()
                        if hasattr(reg_output, "tolist")
                        else reg_output
                    ),
                    "features": feature_dict,
                }

                iteration += 1

        except KeyboardInterrupt:
            print("🛑 Stopping Muse inference loop...")

        finally:
            print("⏹️  Stopping data stream...")
            self.board.stop_stream()

    def disconnect_muse(self):
        """Disconnect from Muse"""
        if self.board:
            self.board.release_session()
            print("Disconnected from Muse")

    def save_results(self, filename: str):
        """Save results history to file"""
        import json

        with open(filename, "w") as f:
            json.dump(self.results_history, f, indent=2)
        print(f"Results saved to {filename}")


def main():
    """Main function for real-time inference"""
    cfg = load_config()

    # Load model
    print("Loading model...")
    model = MultiTaskEEGModel(
        n_channels=cfg.model.n_channels,
        hidden_dims=cfg.model.hidden_dims,
        n_classes=cfg.model.n_classes,
        n_outputs=cfg.model.n_outputs,
    )

    state_dict = torch.load(
        cfg.inference.model_filepath, map_location=cfg.system.accelerator
    )
    new_state_dict = {k.replace("model.", ""): v for k, v in state_dict.items()}
    model.load_state_dict(new_state_dict)
    model.eval()
    print("Model loaded successfully")

    # Initialize Muse interface
    # Or COM7
    muse = MuseRealtimeInference(
        con_port="/dev/ttyACM0" , model=model, cfg=cfg  # Update this to your port
    )

    # Connect to Muse
    print("Connecting to Muse...")
    conn_status = False
    while not conn_status:
        conn_status = muse.connect_muse()
        if not conn_status:
            print("Retrying in 2 seconds...")
            time.sleep(2)

    # Run inference
    try:
        muse.run_realtime_inference(
            burst_duration=1.0,  # 1 second bursts
            max_iterations=None,  # Run indefinitely (use Ctrl+C to stop)
            save_csv="realtime_inference.csv",  # Save in training format
        )
    finally:
        # Save results and disconnect
        timestr = datetime.datetime.now()
        muse.save_results(f"data/inference_results/inference_results_{timestr}.json")
        muse.disconnect_muse()


# at the bottom of muse_inference.py


def start_muse_inference(latest_focus_data):
    """
    Starts the Muse 2 realtime inference loop with a pre-trained multitask model.
    All parameters are hardcoded (no hydra config required).
    """
    cfg = load_config()

    # Hardcoded configuration TODO get from cfg
    # COM_PORT = "/dev/ttyACM0"  # Or COM7
    COM_PORT = cfg.muse.com_port

    # Model architecture parameters
    n_channels = 11
    hidden_dims = [16, 32]
    n_classes = 4
    n_outputs = 4

    print("Loading model...")
    model = MultiTaskEEGModel(
        n_channels=n_channels,
        hidden_dims=hidden_dims,
        n_classes=n_classes,
        n_outputs=n_outputs,
    )

    # Load state dict (with or without "model." prefix)
    state_dict = torch.load(
        Path(cfg.inference.model_filepath).resolve(), map_location="cpu"
    )
    new_state_dict = {k.replace("model.", ""): v for k, v in state_dict.items()}
    model.load_state_dict(new_state_dict)
    model.eval()
    print("✅ Model loaded successfully")

    # Create Muse interface
    muse = MuseRealtimeInference(con_port=cfg.muse.com_port, model=model, cfg=cfg)
    conn_status = False
    while not conn_status:
        try:
            conn_status = muse.connect_muse()
        except Exception as e:
            print(e)
        finally:
            print("\n\n CONNECT SUCCESSFUL! BEGINNING BRAIN PROCESSING \n\n")

    print("🎧 Starting Muse inference loop...")

    # Stream inference results continuously
    for result in muse.run_realtime_inference_generator(burst_duration=1.0):
        latest_focus_data["class_label"] = result["class_label"]
        latest_focus_data["probabilities"] = result["class_probs"]
        latest_focus_data["reg_output"] = result["reg_output"]
        latest_focus_data["timestamp"] = result["timestamp"]


if __name__ == "__main__":
    main()
