from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds, BrainFlowPresets
from brainflow.data_filter import DataFilter, FilterTypes, WindowOperations
import numpy as np
import time
import datetime
import torch
from pathlib import Path
from omegaconf import DictConfig
import hydra
import sys

# Hack to get access to root directory
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))
from training.networks import MultiTaskEEGModel


class MuseRealtimeInference:
    def __init__(self, con_port: str, model, cfg: DictConfig):
        self.con_port = con_port
        self.boardId = 38
        self.board = None
        self.model = model
        self.cfg = cfg
        self.sampling_rate = 256  # Muse2 sampling rate
        self.results_history = []
        
    def connect_muse(self):
        """Connect to Muse headset"""
        try:
            params = BrainFlowInputParams()
            params.serial_port = self.con_port
            self.board = BoardShim(self.boardId, params)
            self.board.prepare_session()
            self.sampling_rate = self.board.get_sampling_rate(self.boardId)
            print(f"Connected to Muse. Sampling rate: {self.sampling_rate} Hz")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            self.board = BoardShim(BoardIds.SYNTHETIC_BOARD)
            self.board.prepare_session()
            self.sampling_rate = self.board.get_sampling_rate(self.boardId)
            print(f"Simulating Fake Muse. Sampling rate: {self.sampling_rate} Hz")
            return False
    
    def get_burst_data(self, duration_seconds: float):
        """
        Get a burst of EEG data and auxiliary data for inference
        
        Args:
            duration_seconds: Duration of data to collect (e.g., 1.0 for 1 second)
        
        Returns:
            eeg_data: numpy array of shape (n_channels, n_samples)
            band_powers: dict with Delta, Theta, Alpha, Beta, Gamma
            gyro_mean: list [x, y, z]
            accel_mean: list [x, y, z]
        """
        # Wait for data to accumulate
        time.sleep(duration_seconds)
        
        # Get data from buffer
        data = self.board.get_board_data()
        
        # Extract EEG channels
        eeg_channels = self.board.get_eeg_channels(self.boardId)
        eeg_data = data[eeg_channels]
        
        # Get auxiliary data (gyro/accel)
        try:
            aux_data = self.board.get_board_data(preset=BrainFlowPresets.AUXILIARY_PRESET)
            if aux_data.shape[0] >= 6:
                accel_data = aux_data[0:3, :]
                gyro_data = aux_data[3:6, :]
                gyro_mean = np.mean(gyro_data, axis=1).tolist()
                accel_mean = np.mean(accel_data, axis=1).tolist()
            else:
                gyro_mean = [0.0, 0.0, 0.0]
                accel_mean = [0.0, 0.0, 0.0]
        except:
            gyro_mean = [0.0, 0.0, 0.0]
            accel_mean = [0.0, 0.0, 0.0]
        
        # Calculate band powers
        if eeg_data.shape[1] % 2 == 1:
            eeg_data_bp = eeg_data[:, :eeg_data.shape[1]-1]
        else:
            eeg_data_bp = eeg_data
        
        eeg_data_bp = np.ascontiguousarray(eeg_data_bp)
        
        try:
            avgs, stds = DataFilter.get_avg_band_powers(
                eeg_data_bp,
                channels=np.arange(eeg_data_bp.shape[0]),
                sampling_rate=self.sampling_rate,
                apply_filter=False
            )
            band_powers = {
                'Delta': avgs[0],
                'Theta': avgs[1],
                'Alpha': avgs[2],
                'Beta': avgs[3],
                'Gamma': avgs[4]
            }
        except:
            band_powers = {
                'Delta': 0.0,
                'Theta': 0.0,
                'Alpha': 0.0,
                'Beta': 0.0,
                'Gamma': 0.0
            }
        
        # Calculate expected samples
        expected_samples = int(duration_seconds * self.sampling_rate)
        
        # Handle case where we got more or less data than expected
        if eeg_data.shape[1] < expected_samples:
            print(f"Warning: Got {eeg_data.shape[1]} samples, expected {expected_samples}")
            # Pad with zeros if needed
            padding = np.zeros((eeg_data.shape[0], expected_samples - eeg_data.shape[1]))
            eeg_data = np.concatenate([eeg_data, padding], axis=1)
        elif eeg_data.shape[1] > expected_samples:
            # Take the most recent samples
            eeg_data = eeg_data[:, -expected_samples:]
        
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
        labels = list(self.cfg.model.labels.keys())
        
        # Model expects 11 channels: [Delta, Theta, Alpha, Beta, Gamma, GyroX, GyroY, GyroZ, AccelX, AccelY, AccelZ]
        # Create feature array by repeating the scalar values across time samples
        n_samples = eeg_data.shape[1]
        
        # Stack all 11 features
        features = np.array([
            np.full(n_samples, band_powers['Delta']),
            np.full(n_samples, band_powers['Theta']),
            np.full(n_samples, band_powers['Alpha']),
            np.full(n_samples, band_powers['Beta']),
            np.full(n_samples, band_powers['Gamma']),
            np.full(n_samples, gyro_mean[0]),
            np.full(n_samples, gyro_mean[1]),
            np.full(n_samples, gyro_mean[2]),
            np.full(n_samples, accel_mean[0]),
            np.full(n_samples, accel_mean[1]),
            np.full(n_samples, accel_mean[2])
        ])  # Shape: (11, n_samples)
        
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
            'Delta': band_powers['Delta'],
            'Theta': band_powers['Theta'],
            'Alpha': band_powers['Alpha'],
            'Beta': band_powers['Beta'],
            'Gamma': band_powers['Gamma'],
            'GyroX': gyro_mean[0],
            'GyroY': gyro_mean[1],
            'GyroZ': gyro_mean[2],
            'AccelX': accel_mean[0],
            'AccelY': accel_mean[1],
            'AccelZ': accel_mean[2],
            'FO-NF': 0.0,  # Placeholder - fill with actual value later
            'FO-FA': 0.0,  # Placeholder - fill with actual value later
            'UF-NF': 0.0,  # Placeholder - fill with actual value later
            'UF-FA': 0.0,  # Placeholder - fill with actual value later
            'Label_Class': class_label
        }
        
        return class_probs, class_label, reg_output, feature_dict
    
    def run_realtime_inference(self, burst_duration: float = 1.0, max_iterations: int = None, save_csv: str = None):
        """
        Run continuous inference loop
        
        Args:
            burst_duration: Duration of each data burst in seconds
            max_iterations: Maximum number of inferences to run (None = infinite)
            save_csv: Optional CSV filename to save results in training format
        """
        if not self.board:
            print("Board not connected!")
            return
        
        print(f"Starting streaming with {burst_duration}s bursts...")
        self.board.start_stream()
        
        # Allow buffer to fill initially
        print("Filling buffer...")
        time.sleep(burst_duration * 2)
        
        # Initialize CSV file if requested
        if save_csv:
            with open(save_csv, 'w') as f:
                headers = "Delta,Theta,Alpha,Beta,Gamma,GyroX,GyroY,GyroZ,AccelX,AccelY,AccelZ,FO-NF,FO-FA,UF-NF,UF-FA,Label_Class"
                f.write(headers + '\n')
        
        iteration = 0
        try:
            while max_iterations is None or iteration < max_iterations:
                # Get burst of data
                eeg_data, band_powers, gyro_mean, accel_mean = self.get_burst_data(burst_duration)
                
                # Run inference
                class_probs, class_label, reg_output, feature_dict = self.predict_state(
                    eeg_data, band_powers, gyro_mean, accel_mean
                )
                
                # Store results
                result = {
                    'timestamp': time.time(),
                    'iteration': iteration,
                    'class_probs': class_probs,
                    'class_label': class_label,
                    'reg_output': reg_output.tolist(),
                    'features': feature_dict
                }
                self.results_history.append(result)
                
                # Save to CSV if requested
                if save_csv:
                    with open(save_csv, 'a') as f:
                        csv_line = f"{feature_dict['Delta']},{feature_dict['Theta']},{feature_dict['Alpha']},{feature_dict['Beta']},{feature_dict['Gamma']},"
                        csv_line += f"{feature_dict['GyroX']},{feature_dict['GyroY']},{feature_dict['GyroZ']},"
                        csv_line += f"{feature_dict['AccelX']},{feature_dict['AccelY']},{feature_dict['AccelZ']},"
                        csv_line += f"{feature_dict['FO-NF']},{feature_dict['FO-FA']},{feature_dict['UF-NF']},{feature_dict['UF-FA']},"
                        csv_line += f"{feature_dict['Label_Class']}"
                        f.write(csv_line + '\n')
                
                # Print results
                print(f"\n--- Iteration {iteration} ---")
                print(f"Predicted State: {class_label}")
                print(f"Probabilities: {class_probs}")
                print(f"Regression Output: {reg_output}")
                
                iteration += 1
                
        except KeyboardInterrupt:
            print("\nStopping inference...")
        finally:
            self.board.stop_stream()
    
    def disconnect_muse(self):
        """Disconnect from Muse"""
        if self.board:
            self.board.release_session()
            print("Disconnected from Muse")
    
    def save_results(self, filename: str):
        """Save results history to file"""
        import json
        with open(filename, 'w') as f:
            json.dump(self.results_history, f, indent=2)
        print(f"Results saved to {filename}")


@hydra.main(config_path="../../configs", config_name="main_config", version_base=None)
def main(cfg: DictConfig):
    """Main function for real-time inference"""
    
    # Load model
    print("Loading model...")
    model = MultiTaskEEGModel(
        n_channels=cfg.model.n_channels,
        hidden_dims=cfg.model.hidden_dims,
        n_classes=cfg.model.n_classes,
        n_outputs=cfg.model.n_outputs,
    )
    
    state_dict = torch.load(cfg.inference.model_filepath, map_location=cfg.system.accelerator)
    new_state_dict = {k.replace("model.", ""): v for k, v in state_dict.items()}
    model.load_state_dict(new_state_dict)
    model.eval()
    print("Model loaded successfully")
    
    # Initialize Muse interface
    muse = MuseRealtimeInference(
        con_port='COM7',  # Update this to your port
        model=model,
        cfg=cfg
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
            save_csv="realtime_inference.csv"  # Save in training format
        )
    finally:
        # Save results and disconnect
        timestr = datetime.datetime.now()
        muse.save_results(f"data/inference_results/inference_results_{timestr}.json")
        muse.disconnect_muse()


if __name__ == "__main__":
    main()